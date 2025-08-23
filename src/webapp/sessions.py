# src/webapp/sessions.py
# --- agent_meta ---
# role: webapp-sessions-router
# owner: @backend
# contract: Роуты для инициализации сессий с обязательной HH авторизацией (user_id + org_id)
# last_reviewed: 2025-08-23
# interfaces:
#   - POST /sessions/init_json (требует HH авторизации)
#   - POST /sessions/init_upload (требует HH авторизации)
# --- /agent_meta ---

from __future__ import annotations

import hashlib
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.webapp.storage_docs import ResumeStore, VacancyStore, SessionStore
from src.hh_adapter.config import HHSettings
from src.hh_adapter.client import HHApiClient
from src.hh_adapter.tokens import HHTokenManager
from src.parsing.resume.pdf_extractor import PdfPlumberExtractor
from src.parsing.resume.parser import LLMResumeParser
from src.parsing.vacancy.parser import HHVacancyParser, VACANCY_ID_RE
from src.auth.hh_middleware import require_hh_connection, UserWithHH
import aiohttp
import asyncio


router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class SessionInitJsonRequest(BaseModel):
    """Запрос на создание сессии с готовыми моделями (без hr_id - используется user context)."""
    resume: Optional[ResumeInfo] = Field(default=None, description="Готовая модель резюме")
    vacancy: Optional[VacancyInfo] = Field(default=None, description="Готовая модель вакансии")
    vacancy_url: Optional[str] = Field(default=None, description="URL вакансии для загрузки")
    reuse_by_hash: bool = Field(default=True, description="Переиспользовать существующие документы по хешу")
    ttl_sec: Optional[int] = Field(default=None, description="Время жизни сессии в секундах")


class SessionInitResponse(BaseModel):
    session_id: str
    resume_id: str
    vacancy_id: str
    resume: ResumeInfo
    vacancy: VacancyInfo
    reused: Dict[str, bool]


# Singleton-инстансы стораджей (без legacy TokenStorage)
_resume_store = ResumeStore()
_vacancy_store = VacancyStore()
_session_store = SessionStore()
_hh_settings = HHSettings()
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(user_key: str) -> asyncio.Lock:
    """Получает блокировку для пользователя (user_id + org_id)."""
    if user_key not in _locks:
        _locks[user_key] = asyncio.Lock()
    return _locks[user_key]


@router.post("/init_json", response_model=SessionInitResponse) 
async def init_session_json(
    req: SessionInitJsonRequest,
    user_context: UserWithHH = Depends(require_hh_connection)
):
    """
    Инициализирует сессию на основе уже готовых моделей (JSON вариант).
    - Если переданы модели, сохраняет их в БД (с дедупликацией по хэшу содержимого при включенном reuse_by_hash).
    - Возвращает session_id и идентификаторы сохранённых документов.

    Примечание: вариант с загрузкой PDF и разбором вакансии по URL будет в отдельном эндпоинте.
    """
    if not req.resume:
        raise HTTPException(status_code=400, detail="Field 'resume' is required for init_json")
    if not req.vacancy and not req.vacancy_url:
        raise HTTPException(status_code=400, detail="Either 'vacancy' or 'vacancy_url' must be provided")

    # Получаем user_key для дедупликации и хранения
    user_key = f"{user_context.user_id}:{user_context.org_id}"
    
    # Резюме: пробуем дедуп по хэшу сериализованной модели
    reused_resume = False
    if req.reuse_by_hash:
        r_hash = _sha256(req.resume.model_dump_json())
        found = _resume_store.find_by_hash(user_key, r_hash)
        if found:
            resume_id, resume_model = found
            reused_resume = True
        else:
            resume_id = _resume_store.save(user_key, req.resume, r_hash)
            resume_model = req.resume
    else:
        resume_id = _resume_store.save(user_key, req.resume, None)
        resume_model = req.resume

    # Вакансия: либо модель передана, либо пока ошибка (URL парсинг добавим позднее)
    if req.vacancy is None:
        # На этом эндпоинте пока не поддерживаем URL-парсинг
        raise HTTPException(status_code=400, detail="vacancy_url is not supported in init_json; provide 'vacancy' model")

    reused_vacancy = False
    if req.reuse_by_hash:
        # Для консистентности считаем хэш по сериализации и используем как source_hash
        v_hash = _sha256(req.vacancy.model_dump_json())
        # source_url неизвестен — используем плейсхолдер
        lookup = _vacancy_store.find_by_url_or_hash(user_key, url="", source_hash=v_hash)
        if lookup:
            vacancy_id, vacancy_model = lookup
            reused_vacancy = True
        else:
            vacancy_id = _vacancy_store.save(user_key, req.vacancy, source_url="", source_hash=v_hash)
            vacancy_model = req.vacancy
    else:
        vacancy_id = _vacancy_store.save(user_key, req.vacancy, source_url="", source_hash=None)
        vacancy_model = req.vacancy

    # Создаем сессию с user_key вместо hr_id
    session_id = _session_store.create(user_key, resume_id, vacancy_id, req.ttl_sec)

    return SessionInitResponse(
        session_id=session_id,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        resume=resume_model,
        vacancy=vacancy_model,
        reused={"resume": reused_resume, "vacancy": reused_vacancy},
    )


@router.post("/init_upload", response_model=SessionInitResponse)
async def init_session_upload(
    vacancy_url: str = Form(...),
    resume_file: UploadFile = File(...),
    reuse_by_hash: bool = Form(True),
    ttl_sec: Optional[int] = Form(default=None),
    user_context: UserWithHH = Depends(require_hh_connection)
):
    """
    Инициализация сессии из сырого ввода: PDF резюме + URL вакансии.
    Дедупликация по хэшам (резюме по извлечённому тексту, вакансия по vacancy_id).
    При отсутствии в БД — выполняет LLM парсинг резюме и загрузку вакансии из HH API.
    """
    # Получаем user_key из контекста авторизации
    user_key = f"{user_context.user_id}:{user_context.org_id}"
    
    # 1) Обработка резюме: читаем bytes, извлекаем текст для хэша
    data = await resume_file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty resume_file")
    text = PdfPlumberExtractor().extract_text(data)
    r_hash = _sha256(text)

    reused_resume = False
    found_resume = _resume_store.find_by_hash(user_key, r_hash) if reuse_by_hash else None
    if found_resume:
        resume_id, resume_model = found_resume
        reused_resume = True
    else:
        # Парсинг через LLM
        resume_model = await LLMResumeParser().parse(data)
        resume_id = _resume_store.save(user_key, resume_model, r_hash if reuse_by_hash else None)

    # 2) Обработка вакансии: получаем vacancy_id из URL, считаем хэш
    m = VACANCY_ID_RE.search(vacancy_url)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid vacancy_url: id not found")
    vacancy_id_norm = m.group(1)

    reused_vacancy = False
    found_vacancy = _vacancy_store.find_by_url_or_hash(user_key, url=vacancy_url, source_hash=vacancy_id_norm) if reuse_by_hash else None
    if found_vacancy:
        vacancy_doc_id, vacancy_model = found_vacancy
        reused_vacancy = True
    else:
        # Используем HH токены из user_context (уже проверены middleware)
        hh_account = user_context.hh_account
        
        expires_in = hh_account.expires_in_seconds
        async with aiohttp.ClientSession() as session:
            # Создаем HHTokenManager из данных аккаунта
            token_manager = HHTokenManager(
                settings=_hh_settings,
                session=session,
                access_token=hh_account.access_token,
                refresh_token=hh_account.refresh_token,
                expires_in=expires_in
            )
            client = HHApiClient(_hh_settings, token_manager, session)
            vacancy_parser = HHVacancyParser()
            vacancy_model = await vacancy_parser.parse_by_url(vacancy_url, client)
            
        vacancy_doc_id = _vacancy_store.save(
            user_key, vacancy_model, source_url=vacancy_url, source_hash=vacancy_id_norm if reuse_by_hash else None
        )

    # 3) Создаём сессию с user_key и возвращаем
    session_id = _session_store.create(user_key, resume_id, vacancy_doc_id, ttl_sec)
    return SessionInitResponse(
        session_id=session_id,
        resume_id=resume_id,
        vacancy_id=vacancy_doc_id,
        resume=resume_model,
        vacancy=vacancy_model,
        reused={"resume": reused_resume, "vacancy": reused_vacancy},
    )
