# tests/auth/test_hh_account_service.py
# --- agent_meta ---
# role: tests-hh-account-service
# owner: @backend
# contract: Unit тесты для HHAccountService (connect, get, disconnect, refresh, is_connected)
# last_reviewed: 2025-08-23
# interfaces:
#   - test_connect_hh_account_saves_tokens()
#   - test_get_hh_account_returns_info()
#   - test_disconnect_hh_account_removes_record()
#   - test_is_hh_connected_checks_expiry()
#   - test_refresh_hh_tokens_updates_storage()
# --- /agent_meta ---

import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from src.auth.storage import AuthStorage
from src.auth.hh_service import HHAccountService, HHAccountInfo


@pytest.fixture
def mock_storage():
    """Мок AuthStorage для изолированных unit тестов."""
    storage = MagicMock(spec=AuthStorage)
    return storage


@pytest.fixture
def hh_service(mock_storage):
    """HHAccountService с мокнутым storage."""
    return HHAccountService(mock_storage)


def test_connect_hh_account_saves_tokens(hh_service, mock_storage):
    """Тест сохранения HH токенов при подключении аккаунта."""
    tokens = {
        "access_token": "test_access",
        "refresh_token": "test_refresh",
        "expires_in": 3600
    }
    
    result = hh_service.connect_hh_account(
        user_id="user123",
        org_id="org456", 
        tokens=tokens,
        scopes="read_resumes",
        ua_hash="ua_hash_value",
        ip_hash="ip_hash_value"
    )
    
    # Проверяем что storage.save_hh_account был вызван с правильными параметрами
    mock_storage.save_hh_account.assert_called_once()
    call_args = mock_storage.save_hh_account.call_args
    
    assert call_args[1]["user_id"] == "user123"
    assert call_args[1]["org_id"] == "org456"
    assert call_args[1]["access_token"] == "test_access"
    assert call_args[1]["refresh_token"] == "test_refresh"
    assert call_args[1]["scopes"] == "read_resumes"
    assert call_args[1]["ua_hash"] == "ua_hash_value"
    assert call_args[1]["ip_hash"] == "ip_hash_value"
    
    # Проверяем возвращаемый объект HHAccountInfo
    assert isinstance(result, HHAccountInfo)
    assert result.user_id == "user123"
    assert result.org_id == "org456"
    assert result.access_token == "test_access"
    assert result.refresh_token == "test_refresh"


def test_connect_hh_account_validates_required_tokens(hh_service):
    """Тест валидации обязательных полей токенов."""
    invalid_tokens = {"access_token": "test"}  # отсутствует refresh_token
    
    with pytest.raises(ValueError, match="Отсутствуют обязательные поля токенов"):
        hh_service.connect_hh_account("user123", "org456", invalid_tokens)


def test_get_hh_account_returns_info(hh_service, mock_storage):
    """Тест получения информации о HH аккаунте."""
    # Мокаем данные из storage
    mock_data = {
        "user_id": "user123",
        "org_id": "org456",
        "access_token": "stored_access",
        "refresh_token": "stored_refresh", 
        "expires_at": time.time() + 1800,
        "scopes": "read_resumes",
        "connected_at": time.time() - 3600,
        "ua_hash": "stored_ua_hash",
        "ip_hash": "stored_ip_hash"
    }
    mock_storage.get_hh_account.return_value = mock_data
    
    result = hh_service.get_hh_account("user123", "org456")
    
    mock_storage.get_hh_account.assert_called_once_with("user123", "org456")
    
    assert isinstance(result, HHAccountInfo)
    assert result.user_id == "user123"
    assert result.org_id == "org456"
    assert result.access_token == "stored_access"
    assert result.refresh_token == "stored_refresh"
    assert result.scopes == "read_resumes"


def test_get_hh_account_returns_none_when_not_found(hh_service, mock_storage):
    """Тест возвращения None когда HH аккаунт не найден."""
    mock_storage.get_hh_account.return_value = None
    
    result = hh_service.get_hh_account("nonexistent", "org456")
    
    assert result is None
    mock_storage.get_hh_account.assert_called_once_with("nonexistent", "org456")


def test_disconnect_hh_account_removes_record(hh_service, mock_storage):
    """Тест удаления HH аккаунта."""
    # Сначала аккаунт существует
    mock_storage.get_hh_account.return_value = {"user_id": "user123", "org_id": "org456"}
    
    result = hh_service.disconnect_hh_account("user123", "org456")
    
    assert result is True
    mock_storage.get_hh_account.assert_called_once_with("user123", "org456")
    mock_storage.delete_hh_account.assert_called_once_with("user123", "org456")


def test_disconnect_hh_account_returns_false_when_not_found(hh_service, mock_storage):
    """Тест обработки отключения несуществующего аккаунта."""
    mock_storage.get_hh_account.return_value = None
    
    result = hh_service.disconnect_hh_account("nonexistent", "org456")
    
    assert result is False
    mock_storage.get_hh_account.assert_called_once_with("nonexistent", "org456")
    mock_storage.delete_hh_account.assert_not_called()


def test_is_hh_connected_checks_expiry(hh_service, mock_storage):
    """Тест проверки подключения с учетом времени истечения токенов."""
    # Случай 1: аккаунт не существует
    mock_storage.get_hh_account.return_value = None
    assert hh_service.is_hh_connected("user123", "org456") is False
    
    # Случай 2: аккаунт существует, токены действительны
    valid_data = {
        "user_id": "user123",
        "org_id": "org456", 
        "access_token": "valid_token",
        "refresh_token": "valid_refresh",
        "expires_at": time.time() + 1800,  # действителен еще 30 минут
        "connected_at": time.time() - 3600
    }
    mock_storage.get_hh_account.return_value = valid_data
    assert hh_service.is_hh_connected("user123", "org456") is True
    
    # Случай 3: аккаунт существует, но токены истекли
    expired_data = {
        "user_id": "user123",
        "org_id": "org456",
        "access_token": "expired_token", 
        "refresh_token": "expired_refresh",
        "expires_at": time.time() - 600,  # истек 10 минут назад
        "connected_at": time.time() - 7200
    }
    mock_storage.get_hh_account.return_value = expired_data
    assert hh_service.is_hh_connected("user123", "org456") is False


@pytest.mark.asyncio
async def test_refresh_hh_tokens_updates_storage(hh_service, mock_storage):
    """Тест обновления токенов через HHTokenManager."""
    # Мокаем существующий HH аккаунт
    existing_account_data = {
        "user_id": "user123",
        "org_id": "org456",
        "access_token": "old_access",
        "refresh_token": "old_refresh",
        "expires_at": time.time() - 300,  # истек 5 минут назад
        "connected_at": time.time() - 3600
    }
    mock_storage.get_hh_account.return_value = existing_account_data
    
    # Мокаем HHTokenManager
    mock_token_manager = MagicMock()
    mock_token_manager.get_valid_access_token = AsyncMock(return_value="new_access_token")
    mock_token_manager.access_token = "new_access_token"
    mock_token_manager.refresh_token = "new_refresh_token"  
    mock_token_manager.expires_at = time.time() + 3600
    
    # Мокаем HHSettings
    mock_settings = MagicMock()
    
    with patch("src.auth.hh_service.aiohttp.ClientSession"), \
         patch("src.auth.hh_service.HHTokenManager", return_value=mock_token_manager), \
         patch("src.auth.hh_service.HHSettings", return_value=mock_settings):
        
        result = await hh_service.refresh_hh_tokens("user123", "org456")
    
    assert result is True
    mock_storage.update_hh_tokens.assert_called_once_with(
        "user123", 
        "org456", 
        {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token", 
            "expires_at": mock_token_manager.expires_at
        }
    )


@pytest.mark.asyncio
async def test_refresh_hh_tokens_handles_missing_account(hh_service, mock_storage):
    """Тест обработки обновления токенов для несуществующего аккаунта."""
    mock_storage.get_hh_account.return_value = None
    
    result = await hh_service.refresh_hh_tokens("nonexistent", "org456")
    
    assert result is False
    mock_storage.update_hh_tokens.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_hh_tokens_handles_token_manager_error(hh_service, mock_storage):
    """Тест обработки ошибки HHTokenManager при обновлении."""
    # Мокаем существующий аккаунт
    existing_account_data = {
        "user_id": "user123",
        "org_id": "org456",
        "access_token": "old_access",
        "refresh_token": "old_refresh", 
        "expires_at": time.time() - 300,
        "connected_at": time.time() - 3600
    }
    mock_storage.get_hh_account.return_value = existing_account_data
    
    # Мокаем HHTokenManager с ошибкой
    mock_token_manager = MagicMock()
    mock_token_manager.get_valid_access_token = AsyncMock(side_effect=Exception("Token refresh failed"))
    
    # Мокаем HHSettings
    mock_settings = MagicMock()
    
    with patch("src.auth.hh_service.aiohttp.ClientSession"), \
         patch("src.auth.hh_service.HHTokenManager", return_value=mock_token_manager), \
         patch("src.auth.hh_service.HHSettings", return_value=mock_settings):
        
        result = await hh_service.refresh_hh_tokens("user123", "org456")
    
    assert result is False
    mock_storage.update_hh_tokens.assert_not_called()


def test_get_connected_users_returns_account_list(hh_service, mock_storage):
    """Тест получения списка пользователей с подключенными HH аккаунтами."""
    mock_accounts_data = [
        {
            "user_id": "user1",
            "org_id": "org1", 
            "access_token": "token1",
            "refresh_token": "refresh1",
            "expires_at": time.time() + 1800,
            "scopes": "read_resumes",
            "connected_at": time.time() - 3600,
            "ua_hash": "ua1",
            "ip_hash": "ip1"
        },
        {
            "user_id": "user2",
            "org_id": "org1",
            "access_token": "token2", 
            "refresh_token": "refresh2",
            "expires_at": time.time() + 2400,
            "scopes": "read_vacancies",
            "connected_at": time.time() - 1800,
            "ua_hash": "ua2",
            "ip_hash": "ip2"
        }
    ]
    mock_storage.list_hh_accounts.return_value = mock_accounts_data
    
    result = hh_service.get_connected_users("org1")
    
    mock_storage.list_hh_accounts.assert_called_once_with("org1")
    assert len(result) == 2
    assert all(isinstance(account, HHAccountInfo) for account in result)
    assert result[0].user_id == "user1"
    assert result[1].user_id == "user2"