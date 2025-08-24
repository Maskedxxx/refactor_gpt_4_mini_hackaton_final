# tests/webapp/test_sessions_upload.py
# --- agent_meta ---
# role: tests-sessions-upload
# owner: @backend
# contract: Тестирует /sessions/init_upload с новой auth архитектурой (session-based + HH middleware)
# last_reviewed: 2025-08-23
# interfaces:
#   - test_init_upload_creates_session_and_persists_models()
#   - test_init_upload_reuse_on_second_call()
#   - test_init_upload_unauthorized_returns_401()
# --- /agent_meta ---

import os
import json

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.auth.hh_service import HHAccountInfo


def _load_test_models() -> tuple[ResumeInfo, VacancyInfo]:
    base = os.path.join(os.path.dirname(__file__), "../data")
    with open(os.path.join(base, "simple_resume.json"), "r", encoding="utf-8") as f:
        resume_data = json.load(f)
    with open(os.path.join(base, "simple_vacancy.json"), "r", encoding="utf-8") as f:
        vac_data = json.load(f)
    return ResumeInfo.model_validate(resume_data), VacancyInfo.model_validate(vac_data)


def _load_pdf_bytes() -> bytes:
    base = os.path.join(os.path.dirname(__file__), "../data")
    with open(os.path.join(base, "resume.pdf"), "rb") as f:
        return f.read()


def _mock_hh_account() -> HHAccountInfo:
    """Создает мок HH аккаунта для тестов."""
    return HHAccountInfo(
        user_id="test-user-1",
        org_id="test-org-1", 
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        expires_at=9999999999.0,
        scopes="read_resumes",
        connected_at=1692000000.0
    )


def _mock_user_context(user_id: str = "test-user-1", org_id: str = "test-org-1"):
    """Создает мок UserWithHH контекста."""
    mock_context = MagicMock()
    mock_context.user_id = user_id
    mock_context.org_id = org_id
    mock_context.session_id = "test-session-123"
    mock_context.hh_account = _mock_hh_account()
    return mock_context


@pytest.mark.asyncio
async def test_init_upload_creates_session_and_persists_models(async_client):
    """Тест создания новой сессии с парсингом резюме и вакансии."""
    resume_model, vacancy_model = _load_test_models()
    pdf_bytes = _load_pdf_bytes()

    # Мокаем зависимости через dependency override
    from src.webapp.app import app
    from src.auth.hh_middleware import require_hh_connection
    
    app.dependency_overrides[require_hh_connection] = lambda: _mock_user_context()
    
    try:
        with patch("src.webapp.sessions.LLMResumeParser") as mock_parser_class, \
             patch("src.parsing.vacancy.parser.HHVacancyParser.parse_by_url", return_value=vacancy_model):
            
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse = AsyncMock(return_value=resume_model)
            mock_parser_class.return_value = mock_parser_instance
            
            resp = await async_client.post(
                "/sessions/init_upload",
                files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
                data={
                    "vacancy_url": "https://hh.ru/vacancy/123456",
                    "reuse_by_hash": "true",
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["reused"] == {"resume": False, "vacancy": False}
    assert data["resume"]["title"] == resume_model.title
    assert data["vacancy"]["name"] == vacancy_model.name
    assert "session_id" in data
    assert "resume_id" in data
    assert "vacancy_id" in data


@pytest.mark.asyncio 
async def test_init_upload_reuse_on_second_call(async_client):
    """Тест переиспользования документов при повторном вызове."""
    resume_model, vacancy_model = _load_test_models()
    pdf_bytes = _load_pdf_bytes()
    
    user_context = _mock_user_context("test-user-2", "test-org-2")

    # Мокаем через dependency override
    from src.webapp.app import app
    from src.auth.hh_middleware import require_hh_connection
    
    app.dependency_overrides[require_hh_connection] = lambda: user_context
    
    try:
        # Первый вызов — создаёт
        with patch("src.webapp.sessions.LLMResumeParser") as mock_parser_class, \
             patch("src.parsing.vacancy.parser.HHVacancyParser.parse_by_url", return_value=vacancy_model):
            
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse = AsyncMock(return_value=resume_model)
            mock_parser_class.return_value = mock_parser_instance
            
            r1 = await async_client.post(
                "/sessions/init_upload",
                files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
                data={
                    "vacancy_url": "https://hh.ru/vacancy/987654",
                    "reuse_by_hash": "true",
                },
            )
        assert r1.status_code == 200, r1.text
        d1 = r1.json()

        # Второй вызов — должен переиспользовать и вернуть те же id
        with patch("src.webapp.sessions.LLMResumeParser") as mock_parser_class, \
             patch("src.parsing.vacancy.parser.HHVacancyParser.parse_by_url", return_value=vacancy_model):
            
            mock_parser_instance = MagicMock()
            mock_parser_instance.parse = AsyncMock(return_value=resume_model)
            mock_parser_class.return_value = mock_parser_instance
            
            r2 = await async_client.post(
                "/sessions/init_upload",
                files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
                data={
                    "vacancy_url": "https://hh.ru/vacancy/987654",
                    "reuse_by_hash": "true",
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert r2.status_code == 200, r2.text
    d2 = r2.json()

    assert d2["reused"]["resume"] is True
    assert d2["reused"]["vacancy"] is True
    assert d1["resume_id"] == d2["resume_id"]
    assert d1["vacancy_id"] == d2["vacancy_id"]


@pytest.mark.asyncio
async def test_init_upload_unauthorized_returns_401(async_client):
    """Тест обработки неавторизованного пользователя (без HH подключения)."""
    pdf_bytes = _load_pdf_bytes()

    # Мокаем middleware через dependency override
    from fastapi import HTTPException
    from src.webapp.app import app
    from src.auth.hh_middleware import require_hh_connection
    
    def mock_require_hh_connection():
        raise HTTPException(status_code=401, detail={"error_code": "HH_NOT_CONNECTED", "message": "HH account not connected"})
    
    app.dependency_overrides[require_hh_connection] = mock_require_hh_connection
    
    try:
        r = await async_client.post(
            "/sessions/init_upload",
            files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "vacancy_url": "https://hh.ru/vacancy/555555",
                "reuse_by_hash": "true",
            },
        )
    finally:
        app.dependency_overrides.clear()
    
    assert r.status_code == 401
    response_detail = r.json()["detail"]
    # Проверяем различные форматы ответа
    if isinstance(response_detail, dict):
        assert response_detail.get("error_code") == "HH_NOT_CONNECTED"
    else:
        assert "HH_NOT_CONNECTED" in str(response_detail) or "HH account not connected" in str(response_detail) or "Unauthorized" in str(response_detail)