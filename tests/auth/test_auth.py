# tests/test_auth.py
# --- agent_meta ---
# role: tests-auth
# owner: @backend
# contract: Интеграционные тесты для модуля аутентификации (signup, login, logout, me, orgs)
# last_reviewed: 2025-08-21
# --- /agent_meta ---

import importlib
import sys
from typing import Generator

import pytest
import httpx


@pytest.fixture()
def app(tmp_path, monkeypatch) -> Generator:
    # Настраиваем окружение до импорта приложения
    db_path = tmp_path / "auth_test.sqlite3"
    monkeypatch.setenv("WEBAPP_DB_PATH", str(db_path))
    monkeypatch.setenv("HH_CLIENT_ID", "test_id")
    monkeypatch.setenv("HH_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("HH_REDIRECT_URI", "http://localhost:8080/auth/hh/callback")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "lax")

    # Гарантируем «чистый» импорт модулей приложения
    for mod in list(sys.modules.keys()):
        if mod.startswith("src.webapp") or mod.startswith("src.auth") or mod.startswith("src.hh_adapter"):
            sys.modules.pop(mod)

    from src.webapp.app import app as fastapi_app

    yield fastapi_app


@pytest.mark.asyncio
async def test_signup_login_logout_me_flow(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1) Signup (auto-login)
        r = await client.post(
            "/auth/signup",
            json={"email": "admin@example.com", "password": "secret123", "org_name": "Demo School"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "user" in data and data["user"]["email"] == "admin@example.com"
        assert "org_id" in data and isinstance(data["org_id"], str)

        # 2) /me доступен (cookie sid установлен)
        r = await client.get("/me")
        assert r.status_code == 200, r.text
        me = r.json()
        assert me["user"]["email"] == "admin@example.com"
        assert me["role"] in {"org_admin", "hr_manager", "recruiter", "viewer"}

        # 3) Повторный signup с тем же email -> 409
        r = await client.post(
            "/auth/signup",
            json={"email": "admin@example.com", "password": "secret123", "org_name": "Demo School"},
        )
        assert r.status_code == 409

        # 4) Logout
        r = await client.post("/auth/logout")
        assert r.status_code == 200

        # 5) /me теперь 401
        r = await client.get("/me")
        assert r.status_code == 401

        # 6) Login снова
        r = await client.post(
            "/auth/login",
            json={"email": "admin@example.com", "password": "secret123"},
        )
        assert r.status_code == 200, r.text

        # 7) /me снова доступен
        r = await client.get("/me")
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_create_org_requires_session_and_returns_id(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Без сессии — 401
        r = await client.post("/orgs", params={"name": "Org2"})
        assert r.status_code == 401

        # Логинимся
        await client.post(
            "/auth/signup",
            json={"email": "owner@example.com", "password": "pw123456", "org_name": "Main"},
        )

        # Создаём новую организацию
        r = await client.post("/orgs", params={"name": "Second Org"})
        assert r.status_code == 200, r.text
        body = r.json()
        assert "org_id" in body and isinstance(body["org_id"], str) and len(body["org_id"]) > 0

