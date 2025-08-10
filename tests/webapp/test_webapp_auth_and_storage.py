# --- agent_meta ---
# role: integration-test
# owner: @backend
# contract: Проверяет start/callback флоу, сохранение токенов и валидацию state
# last_reviewed: 2025-08-10
# dependencies: [pytest, httpx]
# --- /agent_meta ---

import time
from urllib.parse import urlparse, parse_qs

import pytest

from src.webapp.storage import OAuthStateStore, TokenStorage


@pytest.mark.asyncio
async def test_auth_start_saves_state_and_redirects(async_client, app_ctx):
    app_module, db_path = app_ctx

    resp = await async_client.get(
        "/auth/hh/start",
        params={"hr_id": "hr_1", "redirect_to": "http://example.local/ok"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    location = resp.headers["location"]

    parsed = urlparse(location)
    qs = parse_qs(parsed.query)
    assert "client_id" in qs and qs["client_id"][0] == "test_client"
    assert "redirect_uri" in qs
    assert "state" in qs and qs["state"][0]

    state = qs["state"][0]
    # Проверяем, что состояние сохранено в БД и содержит правильные данные
    store = OAuthStateStore(db_path)
    consumed = store.consume(state)
    assert consumed is not None
    assert consumed["hr_id"] == "hr_1"
    assert consumed["redirect_to"] == "http://example.local/ok"


@pytest.mark.asyncio
async def test_callback_exchanges_tokens_and_redirects(monkeypatch, async_client, app_ctx):
    app_module, db_path = app_ctx

    # Сначала создадим валидный state через /start
    start = await async_client.get(
        "/auth/hh/start",
        params={"hr_id": "hr_2", "redirect_to": "http://example.local/back"},
        follow_redirects=False,
    )
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    # Мокаем обмен кода на токены, чтобы не ходить во внешний сервис
    async def fake_exchange(session, settings, code):
        return {
            "access_token": "access_ABC",
            "refresh_token": "refresh_DEF",
            "expires_at": time.time() + 3600,
        }

    # Важно патчить точку использования в модуле приложения, а не определение
    monkeypatch.setattr("src.webapp.app.exchange_code_for_tokens", fake_exchange)

    # Вызываем callback
    cb = await async_client.get(
        "/auth/hh/callback",
        params={"code": "test_code", "state": state},
        follow_redirects=False,
    )

    assert cb.status_code == 302
    assert cb.headers["location"] == "http://example.local/back"

    # Проверяем, что токены сохранились
    storage = TokenStorage(db_path)
    row = storage.get("hr_2")
    assert row is not None
    assert row["access_token"] == "access_ABC"
    assert row["refresh_token"] == "refresh_DEF"
    assert row["expires_at"] > time.time()


@pytest.mark.asyncio
async def test_callback_with_invalid_state_returns_400(async_client):
    resp = await async_client.get(
        "/auth/hh/callback",
        params={"code": "any", "state": "nonexistent"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"].startswith("Invalid or expired state")
