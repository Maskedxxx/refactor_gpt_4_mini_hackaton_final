# src/callback_server/code_handler.py
# --- agent_meta ---
# role: auth-code-file-handler
# owner: @backend
# contract: Manages reading, writing, and cleaning up the auth code file.
# last_reviewed: 2025-07-24
# interfaces:
#   - CodeFileHandler
# --- /agent_meta ---

import os

from src.utils import get_logger

logger = get_logger(__name__)


class CodeFileHandler:
    """Инкапсулирует логику работы с временным файлом для кода авторизации."""

    def __init__(self, file_path: str = ".auth_code"):
        self.file_path = file_path

    def write(self, code: str) -> None:
        """Записывает код в файл."""
        try:
            with open(self.file_path, "w") as f:
                f.write(code)
        except IOError as e:
            logger.error(f"Не удалось записать код в файл {self.file_path}: {e}")
            raise

    def read(self) -> str:
        """Читает код из файла."""
        try:
            with open(self.file_path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning(f"Файл с кодом {self.file_path} не найден.")
            raise
        except IOError as e:
            logger.error(f"Не удалось прочитать код из файла {self.file_path}: {e}")
            raise

    def cleanup(self) -> None:
        """Удаляет файл с кодом, если он существует."""
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
                logger.debug(f"Временный файл с кодом {self.file_path} удален.")
            except OSError as e:
                logger.error(f"Не удалось удалить файл с кодом {self.file_path}: {e}")
                raise

    def exists(self) -> bool:
        """Проверяет, существует ли файл с кодом."""
        return os.path.exists(self.file_path)
