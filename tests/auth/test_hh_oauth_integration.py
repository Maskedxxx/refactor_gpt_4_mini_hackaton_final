# tests/auth/test_hh_oauth_integration.py
# --- agent_meta ---
# role: tests-hh-oauth-integration
# owner: @backend
# contract: Интеграционные тесты для HH OAuth2 flow (connect, callback, status, disconnect)
# last_reviewed: 2025-08-23
# interfaces:
#   - test_hh_connect_generates_auth_url_with_valid_session()
#   - test_hh_connect_fails_without_session()
#   - test_hh_callback_exchanges_code_for_tokens()
#   - test_hh_callback_fails_with_invalid_state()
#   - test_hh_status_shows_connection_info()
#   - test_hh_disconnect_removes_account()
# --- /agent_meta ---

import time
from unittest.mock import patch, AsyncMock, MagicMock
from urllib.parse import urlparse, parse_qs

import pytest
import httpx


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """Настроенное приложение с изолированной БД для auth тестов."""
    db_path = tmp_path / "auth_test.sqlite3"
    monkeypatch.setenv("WEBAPP_DB_PATH", str(db_path))
    monkeypatch.setenv("HH_CLIENT_ID", "test_client_id")
    monkeypatch.setenv("HH_CLIENT_SECRET", "test_client_secret")
    monkeypatch.setenv("HH_REDIRECT_URI", "http://localhost:8080/auth/hh/callback")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "lax")

    # Чистый импорт приложения

    import sys
    for mod in list(sys.modules.keys()):
        if mod.startswith("src.webapp") or mod.startswith("src.auth") or mod.startswith("src.hh_adapter"):
            sys.modules.pop(mod, None)

    from src.webapp.app import app as fastapi_app
    return fastapi_app


@pytest.mark.asyncio
async def test_hh_connect_generates_auth_url_with_valid_session(app):
    """Тест успешного создания OAuth URL для подключения HH аккаунта."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Создаем пользователя и получаем сессию
        await client.post(
            "/auth/signup",
            json={"email": "test@example.com", "password": "password123", "org_name": "Test Org"},
        )

        # 2. Запрашиваем подключение HH аккаунта
        resp = await client.get("/auth/hh/connect")
        
        assert resp.status_code == 200, resp.text
        data = resp.json()
        
        # 3. Проверяем структуру ответа
        assert "auth_url" in data
        assert "state" in data
        assert len(data["state"]) > 20  # Криптографически стойкий state
        
        # 4. Проверяем корректность OAuth URL
        parsed_url = urlparse(data["auth_url"])
        assert parsed_url.netloc == "hh.ru"
        assert parsed_url.path == "/oauth/authorize"
        
        query_params = parse_qs(parsed_url.query)
        assert query_params["response_type"][0] == "code"
        assert query_params["client_id"][0] == "test_client_id"
        assert query_params["redirect_uri"][0] == "http://localhost:8080/auth/hh/callback"
        assert query_params["state"][0] == data["state"]


@pytest.mark.asyncio
async def test_hh_connect_fails_without_session(app):
    """Тест отказа в подключении HH аккаунта без валидной сессии."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/auth/hh/connect")
        
        assert resp.status_code == 401
        error_data = resp.json()["detail"]
        # error_data может быть строкой или dict
        if isinstance(error_data, dict):
            assert error_data["error_code"] == "UNAUTHORIZED"
        else:
            assert "Unauthorized" in error_data or "UNAUTHORIZED" in error_data


@pytest.mark.asyncio
async def test_hh_connect_fails_if_already_connected(app):
    """Тест отказа в подключении если HH аккаунт уже подключен."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Создаем пользователя
        await client.post(
            "/auth/signup",
            json={"email": "existing@example.com", "password": "password123", "org_name": "Test Org"},
        )

        # 2. Мокаем уже подключенный HH аккаунт  
        with patch("src.auth.router._get_hh_service") as mock_get_service:
            mock_hh_service = MagicMock()
            mock_hh_service.is_hh_connected.return_value = True
            mock_get_service.return_value = mock_hh_service
            resp = await client.get("/auth/hh/connect")
            
            assert resp.status_code == 409
            error_data = resp.json()["detail"]
            assert error_data["error_code"] == "HH_ALREADY_CONNECTED"


@pytest.mark.asyncio
async def test_hh_callback_exchanges_code_for_tokens(app):
    """Тест успешного обмена authorization_code на токены в callback."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Создаем пользователя и получаем state через /connect
        await client.post(
            "/auth/signup",
            json={"email": "callback@example.com", "password": "password123", "org_name": "Test Org"},
        )
        
        connect_resp = await client.get("/auth/hh/connect")
        state = connect_resp.json()["state"]

        # 2. Мокаем обмен кода на токены
        mock_tokens = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": time.time() + 3600
        }
        
        with patch("src.auth.router.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_tokens
            
            # 3. Выполняем callback
            resp = await client.get("/auth/hh/callback", params={"code": "test_code", "state": state})
            
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["message"] == "HH account connected successfully"
            assert "user_id" in data
            
            # 4. Проверяем что токены были обменены
            mock_exchange.assert_called_once()


@pytest.mark.asyncio
async def test_hh_callback_fails_with_invalid_state(app):
    """Тест отказа callback при недействительном state."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Попытка callback с несуществующим state
        resp = await client.get("/auth/hh/callback", params={"code": "test_code", "state": "invalid_state"})
        
        assert resp.status_code == 400
        error_data = resp.json()["detail"]
        assert error_data["error_code"] == "INVALID_STATE"


@pytest.mark.asyncio
async def test_hh_status_shows_connection_info(app):
    """Тест получения статуса подключения HH аккаунта."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Создаем пользователя
        await client.post(
            "/auth/signup",
            json={"email": "status@example.com", "password": "password123", "org_name": "Test Org"},
        )

        # 2. Сначала статус должен показывать не подключено
        resp = await client.get("/auth/hh/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_connected"] is False
        assert data["expires_in_seconds"] is None
        assert data["connected_at"] is None

        # 3. Мокаем подключенный аккаунт
        from src.auth.hh_service import HHAccountInfo
        mock_account = HHAccountInfo(
            user_id="test-user",
            org_id="test-org",
            access_token="token",
            refresh_token="refresh",
            expires_at=time.time() + 1800,  # 30 минут
            connected_at=time.time() - 3600  # подключен час назад
        )
        
        with patch("src.auth.router._get_hh_service") as mock_get_service:
            mock_hh_service = MagicMock()
            mock_hh_service.is_hh_connected.return_value = True
            mock_hh_service.get_hh_account.return_value = mock_account
            mock_get_service.return_value = mock_hh_service
            
            resp = await client.get("/auth/hh/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_connected"] is True
            assert data["expires_in_seconds"] == mock_account.expires_in_seconds
            assert data["connected_at"] == mock_account.connected_at


@pytest.mark.asyncio
async def test_hh_disconnect_removes_account(app):
    """Тест отключения HH аккаунта от пользователя."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Создаем пользователя
        await client.post(
            "/auth/signup",
            json={"email": "disconnect@example.com", "password": "password123", "org_name": "Test Org"},
        )

        # 2. Мокаем успешное отключение HH аккаунта
        with patch("src.auth.router._get_hh_service") as mock_get_service:
            mock_hh_service = MagicMock()
            mock_hh_service.disconnect_hh_account.return_value = True
            mock_get_service.return_value = mock_hh_service
            resp = await client.post("/auth/hh/disconnect")
            
            assert resp.status_code == 200
            data = resp.json()
            assert data["message"] == "HH account disconnected successfully"

        # 3. Тест случая когда HH аккаунт не был подключен
        with patch("src.auth.router._get_hh_service") as mock_get_service:
            mock_hh_service = MagicMock()
            mock_hh_service.disconnect_hh_account.return_value = False
            mock_get_service.return_value = mock_hh_service
            resp = await client.post("/auth/hh/disconnect")
            
            assert resp.status_code == 404
            error_data = resp.json()["detail"]
            assert error_data["error_code"] == "HH_NOT_CONNECTED"


@pytest.mark.asyncio
async def test_hh_disconnect_fails_without_session(app):
    """Тест отказа в отключении HH аккаунта без валидной сессии."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/auth/hh/disconnect")
        
        assert resp.status_code == 401
        error_data = resp.json()["detail"]
        # error_data может быть строкой или dict
        if isinstance(error_data, dict):
            assert error_data["error_code"] == "UNAUTHORIZED"
        else:
            assert "Unauthorized" in error_data or "UNAUTHORIZED" in error_data