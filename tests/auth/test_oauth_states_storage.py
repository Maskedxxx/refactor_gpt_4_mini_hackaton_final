# tests/auth/test_oauth_states_storage.py
# --- agent_meta ---
# role: tests-oauth-states-storage
# owner: @backend
# contract: Unit тесты для OAuth states с TTL в AuthStorage
# last_reviewed: 2025-08-23
# interfaces:
#   - test_save_oauth_state_persists_data()
#   - test_get_oauth_state_validates_ttl()
#   - test_delete_oauth_state_consume_pattern()
#   - test_cleanup_expired_oauth_states()
# --- /agent_meta ---

import time
import tempfile
import os

import pytest

from src.auth.storage import AuthStorage


@pytest.fixture
def storage():
    """Изолированный AuthStorage с временной БД для каждого теста."""
    # Создаем временный файл БД
    fd, db_path = tempfile.mkstemp(suffix='.sqlite3')
    os.close(fd)  # Закрываем fd, оставляем только путь
    
    storage = AuthStorage(db_path)
    yield storage
    
    # Очистка после теста
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_save_oauth_state_persists_data(storage):
    """Тест сохранения OAuth state с TTL."""
    state_token = "test_state_12345"
    user_id = "user123"
    org_id = "org456"
    session_id = "session789"
    ua_hash = "ua_hash_value"
    ip_hash = "ip_hash_value"
    ttl_seconds = 600  # 10 минут
    
    # Сохраняем state
    storage.save_oauth_state(
        state=state_token,
        user_id=user_id,
        org_id=org_id,
        session_id=session_id,
        ua_hash=ua_hash,
        ip_hash=ip_hash,
        ttl_seconds=ttl_seconds
    )
    
    # Проверяем что state сохранился и можем его получить
    retrieved = storage.get_oauth_state(state_token)
    
    assert retrieved is not None
    assert retrieved["user_id"] == user_id
    assert retrieved["org_id"] == org_id
    assert retrieved["session_id"] == session_id
    assert retrieved["ua_hash"] == ua_hash
    assert retrieved["ip_hash"] == ip_hash
    
    # Проверяем что expires_at установлен корректно (с погрешностью в 5 секунд)
    expected_expires_at = time.time() + ttl_seconds
    assert abs(retrieved["expires_at"] - expected_expires_at) < 5


def test_get_oauth_state_validates_ttl(storage):
    """Тест автоматического удаления истекших OAuth states."""
    state_token = "expired_state"
    
    # Сохраняем state с коротким TTL (1 секунда)
    storage.save_oauth_state(
        state=state_token,
        user_id="user123",
        org_id="org456", 
        session_id="session789",
        ttl_seconds=1
    )
    
    # Сразу после создания state должен быть доступен
    retrieved = storage.get_oauth_state(state_token)
    assert retrieved is not None
    
    # Ждем истечения TTL
    time.sleep(1.1)
    
    # После истечения TTL state должен автоматически удалиться
    retrieved_after_expiry = storage.get_oauth_state(state_token)
    assert retrieved_after_expiry is None


def test_get_oauth_state_returns_none_for_nonexistent(storage):
    """Тест возврата None для несуществующего state."""
    result = storage.get_oauth_state("nonexistent_state")
    assert result is None


def test_delete_oauth_state_consume_pattern(storage):
    """Тест удаления OAuth state (consume pattern)."""
    state_token = "consumable_state"
    
    # Сохраняем state
    storage.save_oauth_state(
        state=state_token,
        user_id="user123",
        org_id="org456",
        session_id="session789",
        ttl_seconds=600
    )
    
    # Проверяем что state существует
    assert storage.get_oauth_state(state_token) is not None
    
    # Удаляем (consume) state
    deleted = storage.delete_oauth_state(state_token)
    assert deleted is True
    
    # После удаления state больше не доступен
    assert storage.get_oauth_state(state_token) is None
    
    # Повторная попытка удаления возвращает False
    deleted_again = storage.delete_oauth_state(state_token)
    assert deleted_again is False


def test_cleanup_expired_oauth_states(storage):
    """Тест массовой очистки истекших OAuth states."""
    # Создаем несколько states: 2 действительных, 2 истекших
    
    # Действительные states (TTL 600 секунд)
    storage.save_oauth_state("valid_state_1", "user1", "org1", "session1", ttl_seconds=600)
    storage.save_oauth_state("valid_state_2", "user2", "org2", "session2", ttl_seconds=600)
    
    # Истекшие states - сохраняем с отрицательным TTL (хак для теста)
    storage.save_oauth_state("expired_state_1", "user3", "org3", "session3", ttl_seconds=-10)
    storage.save_oauth_state("expired_state_2", "user4", "org4", "session4", ttl_seconds=-20)
    
    # Проверяем действительные states
    assert storage.get_oauth_state("valid_state_1") is not None
    assert storage.get_oauth_state("valid_state_2") is not None
    
    # Выполняем cleanup
    deleted_count = storage.cleanup_expired_oauth_states()
    
    # Должны быть удалены 2 истекших state
    assert deleted_count == 2
    
    # Действительные states остаются доступными
    assert storage.get_oauth_state("valid_state_1") is not None
    assert storage.get_oauth_state("valid_state_2") is not None


def test_oauth_state_security_fields(storage):
    """Тест сохранения полей безопасности (ua_hash, ip_hash)."""
    state_token = "security_test_state"
    
    # Сохраняем state без полей безопасности
    storage.save_oauth_state(
        state=state_token,
        user_id="user123",
        org_id="org456",
        session_id="session789"
    )
    
    retrieved = storage.get_oauth_state(state_token)
    assert retrieved["ua_hash"] is None
    assert retrieved["ip_hash"] is None
    
    # Удаляем и создаем заново с полями безопасности
    storage.delete_oauth_state(state_token)
    
    storage.save_oauth_state(
        state=state_token,
        user_id="user123",
        org_id="org456", 
        session_id="session789",
        ua_hash="user_agent_hash",
        ip_hash="ip_address_hash"
    )
    
    retrieved_with_security = storage.get_oauth_state(state_token)
    assert retrieved_with_security["ua_hash"] == "user_agent_hash"
    assert retrieved_with_security["ip_hash"] == "ip_address_hash"