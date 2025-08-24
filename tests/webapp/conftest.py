# --- agent_meta ---
# role: test-fixtures
# owner: @backend
# contract: Фикстуры для webapp: изолированная БД, окружение для auth + HH, httpx AsyncClient
# last_reviewed: 2025-08-24
# --- /agent_meta ---

import importlib
import sys
import types
from typing import Generator, Tuple

import pytest
import httpx


@pytest.fixture()
def app_ctx(tmp_path, monkeypatch) -> Generator[Tuple[types.ModuleType, str], None, None]:
    """
    Инициализирует окружение для webapp с отдельной SQLite БД для AuthStorage.
    Настраивает переменные окружения для новой auth архитектуры.
    """
    db_path = tmp_path / "app.sqlite3"

    # Окружение для новой auth системы
    monkeypatch.setenv("WEBAPP_DB_PATH", str(db_path))
    monkeypatch.setenv("HH_CLIENT_ID", "test_client")
    monkeypatch.setenv("HH_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("HH_REDIRECT_URI", "http://localhost/auth/hh/callback")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUTH_COOKIE_SAMESITE", "lax")

    # Гарантируем «чистый» импорт модулей для изолированных тестов
    for mod in list(sys.modules.keys()):
        if mod.startswith("src.webapp") or mod.startswith("src.auth") or mod.startswith("src.hh_adapter"):
            sys.modules.pop(mod, None)

    # Импортируем webapp с новыми настройками
    app_module = importlib.import_module("src.webapp.app")

    yield app_module, str(db_path)


@pytest.fixture()
async def async_client(app_ctx):
    """AsyncClient для интеграционных тестов webapp с мок-авторизацией."""
    app_module, _ = app_ctx
    
    # Автоматически настраиваем dependency override для HH авторизации
    from src.auth.hh_middleware import require_hh_connection, UserWithHH
    from src.auth.hh_service import HHAccountInfo
    
    # Создаем mock HH account
    mock_hh_account = HHAccountInfo(
        user_id="test-user-webapp",
        org_id="test-org-webapp", 
        access_token="mock-access-token",
        refresh_token="mock-refresh-token",
        expires_at=9999999999  # Far in the future
    )
    
    # Создаем mock user context
    mock_user = UserWithHH(
        user_id="test-user-webapp",
        org_id="test-org-webapp",
        user_email="test@webapp.com", 
        user_role="admin",
        hh_account=mock_hh_account,
        session_id="mock-session-webapp"
    )
    
    def mock_require_hh_connection():
        return mock_user
    
    # Override dependency в FastAPI приложении
    app_module.app.dependency_overrides[require_hh_connection] = mock_require_hh_connection
    
    try:
        transport = httpx.ASGITransport(app=app_module.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
    finally:
        # Очищаем dependency overrides после тестов
        app_module.app.dependency_overrides.clear()

