# tests/callback_server/test_code_handler.py
# --- agent_meta ---
# role: unit-test
# owner: @backend
# contract: Validates the logic of CodeFileHandler for file operations.
# last_reviewed: 2025-08-05
# dependencies: [pytest]
# --- /agent_meta ---

import os
import pytest
from src.callback_server.code_handler import CodeFileHandler

@pytest.fixture
def handler():
    """Фикстура для создания экземпляра CodeFileHandler с временным файлом."""
    # Используем уникальное имя файла для каждого теста, чтобы избежать конфликтов
    test_file_path = ".test_auth_code"
    h = CodeFileHandler(file_path=test_file_path)
    
    # Перед тестом убедимся, что файла нет
    h.cleanup()
    
    yield h
    
    # После теста гарантированно очищаем за собой
    h.cleanup()

def test_write_read_cleanup_flow(handler: CodeFileHandler):
    """Тестирует основной сценарий: запись, чтение, проверка существования и очистка."""
    # 1. Изначально файла не существует
    assert not handler.exists()

    # 2. Записываем код
    test_code = "my-secret-test-code-123"
    handler.write(test_code)

    # 3. Теперь файл должен существовать
    assert handler.exists()
    assert os.path.exists(handler.file_path)

    # 4. Читаем код и проверяем, что он совпадает
    read_code = handler.read()
    assert read_code == test_code

    # 5. Очищаем файл
    handler.cleanup()

    # 6. Файл больше не должен существовать
    assert not handler.exists()

def test_read_non_existent_file_raises_error(handler: CodeFileHandler):
    """Тестирует, что чтение несуществующего файла вызывает FileNotFoundError."""
    # Убедимся, что файла нет
    assert not handler.exists()
    
    # Проверяем, что вызов read() вызывает ожидаемое исключение
    with pytest.raises(FileNotFoundError):
        handler.read()
