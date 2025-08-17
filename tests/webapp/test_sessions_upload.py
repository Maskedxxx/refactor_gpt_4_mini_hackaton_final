# tests/webapp/test_sessions_upload.py
# --- agent_meta ---
# role: tests-sessions-upload
# owner: @backend
# contract: Тестирует /sessions/init_upload (multipart) с дедупликацией и токенами HH
# last_reviewed: 2025-08-17
# interfaces:
#   - test_init_upload_creates_session_and_persists_models()
#   - test_init_upload_reuse_on_second_call()
#   - test_init_upload_unauthorized_hr_returns_401()
# --- /agent_meta ---

import os
import json
from typing import Any

import pytest
from unittest.mock import patch

from src.webapp.models import TokenRecord
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo


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


@pytest.mark.asyncio
async def test_init_upload_creates_session_and_persists_models(async_client):
    resume_model, vacancy_model = _load_test_models()
    pdf_bytes = _load_pdf_bytes()

    # Патчим LLM и HH парсеры, чтобы не ходить наружу
    with patch("src.webapp.sessions.LLMResumeParser.__init__", return_value=None), \
         patch("src.webapp.sessions.LLMResumeParser.parse", return_value=resume_model), \
         patch("src.webapp.sessions.HHVacancyParser.parse_by_url", return_value=vacancy_model), \
         patch("src.webapp.sessions._tokens.get_record", return_value=TokenRecord(access_token="a", refresh_token="b", expires_at=9999999999.0)):
        resp = await async_client.post(
            "/sessions/init_upload",
            files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "hr_id": "hr-u-1",
                "vacancy_url": "https://hh.ru/vacancy/123456",
                "reuse_by_hash": "true",
            },
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["reused"] == {"resume": False, "vacancy": False}
    assert data["resume"]["title"] == resume_model.title
    assert data["vacancy"]["name"] == vacancy_model.name


@pytest.mark.asyncio
async def test_init_upload_reuse_on_second_call(async_client):
    resume_model, vacancy_model = _load_test_models()
    pdf_bytes = _load_pdf_bytes()

    # Первый вызов — создаёт
    with patch("src.webapp.sessions.LLMResumeParser.__init__", return_value=None), \
         patch("src.webapp.sessions.LLMResumeParser.parse", return_value=resume_model), \
         patch("src.webapp.sessions.HHVacancyParser.parse_by_url", return_value=vacancy_model), \
         patch("src.webapp.sessions._tokens.get_record", return_value=TokenRecord(access_token="a", refresh_token="b", expires_at=9999999999.0)):
        r1 = await async_client.post(
            "/sessions/init_upload",
            files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "hr_id": "hr-u-2",
                "vacancy_url": "https://hh.ru/vacancy/987654",
                "reuse_by_hash": "true",
            },
        )
    assert r1.status_code == 200, r1.text
    d1 = r1.json()

    # Второй вызов — должен переиспользовать и вернуть те же id
    with patch("src.webapp.sessions.LLMResumeParser.parse", return_value=resume_model), \
         patch("src.webapp.sessions.HHVacancyParser.parse_by_url", return_value=vacancy_model), \
         patch("src.webapp.sessions._tokens.get_record", return_value=TokenRecord(access_token="a", refresh_token="b", expires_at=9999999999.0)):
        r2 = await async_client.post(
            "/sessions/init_upload",
            files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "hr_id": "hr-u-2",
                "vacancy_url": "https://hh.ru/vacancy/987654",
                "reuse_by_hash": "true",
            },
        )
    assert r2.status_code == 200, r2.text
    d2 = r2.json()

    assert d2["reused"]["resume"] is True
    assert d2["reused"]["vacancy"] is True
    assert d1["resume_id"] == d2["resume_id"]
    assert d1["vacancy_id"] == d2["vacancy_id"]


@pytest.mark.asyncio
async def test_init_upload_unauthorized_hr_returns_401(async_client):
    resume_model, vacancy_model = _load_test_models()
    pdf_bytes = _load_pdf_bytes()

    # Токенов нет — должен вернуться 401, если дедуп не нашёлся
    with patch("src.webapp.sessions.LLMResumeParser.__init__", return_value=None), \
         patch("src.webapp.sessions.LLMResumeParser.parse", return_value=resume_model), \
         patch("src.webapp.sessions.HHVacancyParser.parse_by_url", return_value=vacancy_model), \
         patch("src.webapp.sessions._tokens.get_record", return_value=None):
        r = await async_client.post(
            "/sessions/init_upload",
            files={"resume_file": ("resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "hr_id": "hr-u-unauth",
                "vacancy_url": "https://hh.ru/vacancy/555555",
                "reuse_by_hash": "true",
            },
        )
    assert r.status_code == 401
    assert "authorized" in r.text or "HR not authorized" in r.text
