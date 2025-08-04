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
        logger.debug("Инициализирован CodeFileHandler для файла: %s", file_path)

    def write(self, code: str) -> None:
        """Записывает код в файл."""
        logger.debug("Запись кода авторизации в файл %s", self.file_path)
        try:
            with open(self.file_path, "w") as f:
                f.write(code)
            logger.info("Код авторизации успешно сохранен в файл")
        except IOError as e:
            logger.error("Не удалось записать код в файл %s: %s", self.file_path, e)
            raise

    def read(self) -> str:
        """Читает код из файла."""
        logger.debug("Чтение кода авторизации из файла %s", self.file_path)
        try:
            with open(self.file_path, "r") as f:
                code = f.read().strip()
                logger.info("Код авторизации успешно прочитан из файла")
                return code
        except FileNotFoundError:
            logger.warning("Файл с кодом %s не найден", self.file_path)
            raise
        except IOError as e:
            logger.error("Не удалось прочитать код из файла %s: %s", self.file_path, e)
            raise

    def cleanup(self) -> None:
        """Удаляет файл с кодом, если он существует."""
        if os.path.exists(self.file_path):
            logger.debug("Удаление временного файла с кодом %s", self.file_path)
            try:
                os.remove(self.file_path)
                logger.debug("Временный файл с кодом %s успешно удален", self.file_path)
            except OSError as e:
                logger.error("Не удалось удалить файл с кодом %s: %s", self.file_path, e)
                raise
        else:
            logger.debug("Файл %s не существует, очистка не требуется", self.file_path)

    def exists(self) -> bool:
        """Проверяет, существует ли файл с кодом."""
        exists = os.path.exists(self.file_path)
        logger.debug("Проверка существования файла %s: %s", self.file_path, "существует" if exists else "не существует")
        return exists
