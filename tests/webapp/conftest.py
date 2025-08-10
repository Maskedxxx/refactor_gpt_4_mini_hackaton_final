# --- agent_meta ---
# role: test-fixtures
# owner: @backend
# contract: Фикстуры для webapp: изолированная БД, окружение HH_*, httpx AsyncClient
# last_reviewed: 2025-08-10
# --- /agent_meta ---

import os
import importlib
import types
from typing import Generator, Tuple

import pytest
import httpx


@pytest.fixture()
def app_ctx(tmp_path, monkeypatch) -> Generator[Tuple[types.ModuleType, str], None, None]:
    """
    Инициализирует окружение для webapp с отдельной SQLite БД и настраивает HH_* env vars.
    Возвращает кортеж (модуль webapp.app, путь к БД).
    """
    db_path = tmp_path / "app.sqlite3"

    # Окружение для настроек HH
    monkeypatch.setenv("HH_CLIENT_ID", "test_client")
    monkeypatch.setenv("HH_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("HH_REDIRECT_URI", "http://localhost/auth/hh/callback")
    # Указываем путь БД для webapp storage/state
    monkeypatch.setenv("WEBAPP_DB_PATH", str(db_path))

    # Импортируем/перезагружаем модуль, чтобы подхватил env
    if "src.webapp.app" in importlib.sys.modules:
        importlib.reload(importlib.import_module("src.webapp.app"))
    app_module = importlib.import_module("src.webapp.app")

    yield app_module, str(db_path)


@pytest.fixture()
async def async_client(app_ctx):
    app_module, _ = app_ctx
    transport = httpx.ASGITransport(app=app_module.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

