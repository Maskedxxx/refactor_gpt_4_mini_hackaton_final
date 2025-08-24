# tests/webapp/test_sessions_and_features.py
# --- agent_meta ---
# role: tests-sessions-and-features
# owner: @backend
# contract: Покрывает JSON-инициализацию сессии и генерацию фич по session_id
# last_reviewed: 2025-08-17
# interfaces:
#   - test_init_json_creates_session_and_persists_models()
#   - test_init_json_deduplicates_on_second_call()
#   - test_features_generate_uses_session_models()
# --- /agent_meta ---

import os
import json
from typing import Any

import pytest
from unittest.mock import MagicMock, AsyncMock

from tests.webapp.conftest import async_client, app_ctx  # noqa: F401


def _load_test_data() -> tuple[dict[str, Any], dict[str, Any]]:
    base = os.path.join(os.path.dirname(__file__), "../data")
    with open(os.path.join(base, "simple_resume.json"), "r", encoding="utf-8") as f:
        resume = json.load(f)
    with open(os.path.join(base, "simple_vacancy.json"), "r", encoding="utf-8") as f:
        vacancy = json.load(f)
    return resume, vacancy


@pytest.mark.asyncio
async def test_init_json_creates_session_and_persists_models(async_client):
    # HH подключение теперь автоматически настраивается в async_client фикстуре
    resume, vacancy = _load_test_data()
    payload = {
        "resume": resume,
        "vacancy": vacancy,
        # reuse_by_hash по умолчанию True
    }

    resp = await async_client.post("/sessions/init_json", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Базовые проверки ответа
    assert "session_id" in data and data["session_id"]
    assert "resume_id" in data and data["resume_id"]
    assert "vacancy_id" in data and data["vacancy_id"]
    assert data["reused"] == {"resume": False, "vacancy": False}

    # Схемы вернулись обратно корректно
    assert data["resume"]["title"] == resume["title"]
    assert data["vacancy"]["name"] == vacancy["name"]


@pytest.mark.asyncio
async def test_init_json_deduplicates_on_second_call(async_client):
    # HH подключение теперь автоматически настраивается в async_client фикстуре
    resume, vacancy = _load_test_data()
    base_payload = {
        "resume": resume,
        "vacancy": vacancy,
    }

    # Первый вызов — создаёт
    r1 = await async_client.post("/sessions/init_json", json=base_payload)
    assert r1.status_code == 200, r1.text
    d1 = r1.json()

    # Повторный вызов — должен переиспользовать
    r2 = await async_client.post("/sessions/init_json", json=base_payload)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()

    assert d2["reused"]["resume"] is True
    assert d2["reused"]["vacancy"] is True
    # Идентификаторы должны совпасть (reuse)
    assert d1["resume_id"] == d2["resume_id"]
    assert d1["vacancy_id"] == d2["vacancy_id"]


class _MockGen:
    def __init__(self):
        self.generate = AsyncMock(return_value={"ok": True})


@pytest.mark.asyncio
async def test_features_generate_uses_session_models(async_client):
    # HH подключение теперь автоматически настраивается в async_client фикстуре
    resume, vacancy = _load_test_data()
    init_payload = {
        "resume": resume,
        "vacancy": vacancy,
    }
    # Создаём сессию
    init_resp = await async_client.post("/sessions/init_json", json=init_payload)
    assert init_resp.status_code == 200, init_resp.text
    session_id = init_resp.json()["session_id"]

    # Подготовим мок-реестр
    mock_registry = MagicMock()
    mock_gen = _MockGen()
    mock_registry.get_generator.return_value = mock_gen

    from unittest.mock import patch
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        feat_resp = await async_client.post(
            "/features/test_feature/generate",
            json={
                "session_id": session_id,
                "options": {"temperature": 0.2},
            },
        )

    assert feat_resp.status_code == 200, feat_resp.text
    # Проверяем, что генератор был вызван с моделями (а не None)
    args, kwargs = mock_gen.generate.call_args
    # Генерация вызывается с именованными параметрами
    assert kwargs.get("resume") is not None and kwargs.get("vacancy") is not None
