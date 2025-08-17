# src/webapp/sessions.py
# --- agent_meta ---
# role: webapp-sessions-router
# owner: @backend
# contract: Роуты для инициализации сессий (сохранение ResumeInfo/VacancyInfo в БД)
# last_reviewed: 2025-08-17
# interfaces:
#   - POST /sessions/init_json
# --- /agent_meta ---

from __future__ import annotations

import hashlib
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.webapp.storage_docs import ResumeStore, VacancyStore, SessionStore
from src.webapp.storage import TokenStorage
from src.webapp.service import PersistentTokenManager
from src.hh_adapter.config import HHSettings
from src.hh_adapter.client import HHApiClient
from src.parsing.resume.pdf_extractor import PdfPlumberExtractor
from src.parsing.resume.parser import LLMResumeParser
from src.parsing.vacancy.parser import HHVacancyParser, VACANCY_ID_RE
import aiohttp
import asyncio


router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class SessionInitJsonRequest(BaseModel):
    hr_id: str
    resume: Optional[ResumeInfo] = Field(default=None, description="Готовая модель резюме")
    vacancy: Optional[VacancyInfo] = Field(default=None, description="Готовая модель вакансии")
    vacancy_url: Optional[str] = Field(default=None, description="URL вакансии (пока не используется в этом эндпоинте)")
    reuse_by_hash: bool = Field(default=True)
    ttl_sec: Optional[int] = Field(default=None)


class SessionInitResponse(BaseModel):
    session_id: str
    resume_id: str
    vacancy_id: str
    resume: ResumeInfo
    vacancy: VacancyInfo
    reused: Dict[str, bool]


# Простые singleton-инстансы стораджей для роутера
_resume_store = ResumeStore()
_vacancy_store = VacancyStore()
_session_store = SessionStore()
_tokens = TokenStorage()
_hh_settings = HHSettings()
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(hr_id: str) -> asyncio.Lock:
    if hr_id not in _locks:
        _locks[hr_id] = asyncio.Lock()
    return _locks[hr_id]


@router.post("/init_json", response_model=SessionInitResponse)
async def init_session_json(req: SessionInitJsonRequest):
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

    # Резюме: пробуем дедуп по хэшу сериализованной модели
    reused_resume = False
    if req.reuse_by_hash:
        r_hash = _sha256(req.resume.model_dump_json())
        found = _resume_store.find_by_hash(req.hr_id, r_hash)
        if found:
            resume_id, resume_model = found
            reused_resume = True
        else:
            resume_id = _resume_store.save(req.hr_id, req.resume, r_hash)
            resume_model = req.resume
    else:
        resume_id = _resume_store.save(req.hr_id, req.resume, None)
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
        lookup = _vacancy_store.find_by_url_or_hash(req.hr_id, url="", source_hash=v_hash)
        if lookup:
            vacancy_id, vacancy_model = lookup
            reused_vacancy = True
        else:
            vacancy_id = _vacancy_store.save(req.hr_id, req.vacancy, source_url="", source_hash=v_hash)
            vacancy_model = req.vacancy
    else:
        vacancy_id = _vacancy_store.save(req.hr_id, req.vacancy, source_url="", source_hash=None)
        vacancy_model = req.vacancy

    session_id = _session_store.create(req.hr_id, resume_id, vacancy_id, req.ttl_sec)

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
    hr_id: str = Form(...),
    vacancy_url: str = Form(...),
    resume_file: UploadFile = File(...),
    reuse_by_hash: bool = Form(True),
    ttl_sec: Optional[int] = Form(default=None),
):
    """
    Инициализация сессии из сырого ввода: PDF резюме + URL вакансии.
    Дедупликация по хэшам (резюме по извлечённому тексту, вакансия по vacancy_id).
    При отсутствии в БД — выполняет LLM парсинг резюме и загрузку вакансии из HH API.
    """
    # 1) Обработка резюме: читаем bytes, извлекаем текст для хэша
    data = await resume_file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty resume_file")
    text = PdfPlumberExtractor().extract_text(data)
    r_hash = _sha256(text)

    reused_resume = False
    found_resume = _resume_store.find_by_hash(hr_id, r_hash) if reuse_by_hash else None
    if found_resume:
        resume_id, resume_model = found_resume
        reused_resume = True
    else:
        # Парсинг через LLM
        resume_model = await LLMResumeParser().parse(data)
        resume_id = _resume_store.save(hr_id, resume_model, r_hash if reuse_by_hash else None)

    # 2) Обработка вакансии: получаем vacancy_id из URL, считаем хэш
    m = VACANCY_ID_RE.search(vacancy_url)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid vacancy_url: id not found")
    vacancy_id_norm = m.group(1)

    reused_vacancy = False
    found_vacancy = _vacancy_store.find_by_url_or_hash(hr_id, url=vacancy_url, source_hash=vacancy_id_norm) if reuse_by_hash else None
    if found_vacancy:
        vacancy_doc_id, vacancy_model = found_vacancy
        reused_vacancy = True
    else:
        # Нужны токены для HR
        record = _tokens.get_record(hr_id)
        if not record:
            raise HTTPException(status_code=401, detail="HR not authorized for HH API")

        expires_in = max(0, int(float(record.expires_at)))
        async with aiohttp.ClientSession() as session:
            manager = PersistentTokenManager(
                hr_id=hr_id,
                storage=_tokens,
                settings=_hh_settings,
                session=session,
                access_token=record.access_token,
                refresh_token=record.refresh_token,
                expires_in=expires_in,
                lock=_get_lock(hr_id),
            )
            client = HHApiClient(_hh_settings, manager, session)
            vacancy_parser = HHVacancyParser()
            vacancy_model = await vacancy_parser.parse_by_url(vacancy_url, client)
        vacancy_doc_id = _vacancy_store.save(
            hr_id, vacancy_model, source_url=vacancy_url, source_hash=vacancy_id_norm if reuse_by_hash else None
        )

    # 3) Создаём сессию и возвращаем
    session_id = _session_store.create(hr_id, resume_id, vacancy_doc_id, ttl_sec)
    return SessionInitResponse(
        session_id=session_id,
        resume_id=resume_id,
        vacancy_id=vacancy_doc_id,
        resume=resume_model,
        vacancy=vacancy_model,
        reused={"resume": reused_resume, "vacancy": reused_vacancy},
    )
