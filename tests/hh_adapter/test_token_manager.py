# tests/hh_adapter/test_token_manager.py
# --- agent_meta ---
# role: unit-test
# owner: @backend
# contract: Validates the token lifecycle logic in HHTokenManager using mocks.
# last_reviewed: 2025-08-05
# dependencies: [pytest, pytest-asyncio, pytest-mock]
# --- /agent_meta ---

import time
import pytest
from unittest.mock import AsyncMock

from src.hh_adapter.tokens import HHTokenManager
from src.hh_adapter.config import HHSettings

# Для тестов нам не нужна реальная сессия, поэтому используем мок.
# Также создаем базовые настройки.
@pytest.fixture
def mock_session():
    """Фикстура для создания мока aiohttp.ClientSession."""
    return AsyncMock()

@pytest.fixture
def hh_settings():
    """Фикстура для создания базовых настроек HH.ru."""
    return HHSettings(client_id="test_id", client_secret="test_secret", redirect_uri="http://localhost/cb")

@pytest.mark.asyncio
async def test_get_valid_token_uses_existing_if_valid(hh_settings, mock_session):
    """Тест: если токен валиден, он должен быть возвращен без обновления."""
    # Создаем менеджер с токеном, который будет валиден еще долго
    manager = HHTokenManager(
        settings=hh_settings,
        session=mock_session,
        access_token="valid_token",
        refresh_token="any_refresh_token",
        expires_in=3600  # Истекает через час
    )

    # "Шпионим" за методом _refresh_token, чтобы убедиться, что он НЕ будет вызван
    manager._refresh_token = AsyncMock()

    token = await manager.get_valid_access_token()

    # Проверяем, что вернулся наш существующий токен
    assert token == "valid_token"
    # Проверяем, что метод обновления НЕ вызывался
    manager._refresh_token.assert_not_called()

@pytest.mark.asyncio
async def test_get_valid_token_refreshes_if_expired(hh_settings, mock_session):
    """Тест: если токен истек, должен быть вызван метод обновления."""
    # Создаем менеджер с истекшим токеном (expires_in=0)
    manager = HHTokenManager(
        settings=hh_settings,
        session=mock_session,
        access_token="expired_token",
        refresh_token="any_refresh_token",
        expires_in=0 # Токен уже истек
    )

    # Мокаем (заменяем) метод _refresh_token, чтобы он не делал реальный запрос.
    # Также настроим его так, чтобы он "обновлял" токен в менеджере.
    async def mock_refresh():
        manager._update_tokens({
            "access_token": "new_refreshed_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        })
    
    manager._refresh_token = AsyncMock(side_effect=mock_refresh)

    token = await manager.get_valid_access_token()

    # Проверяем, что метод обновления был вызван ровно один раз
    manager._refresh_token.assert_called_once()
    # Проверяем, что мы получили новый, "обновленный" токен
    assert token == "new_refreshed_token"
