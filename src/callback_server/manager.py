# src/callback_server/manager.py
# --- agent_meta ---
# role: callback-server-manager
# owner: @backend
# contract: Manages the lifecycle of the callback server.
# last_reviewed: 2025-07-24
# interfaces:
#   - ServerManager
# --- /agent_meta ---

import asyncio
import sys
import threading

import uvicorn

from src.callback_server.code_handler import CodeFileHandler
from src.callback_server.config import CallbackServerSettings
from src.callback_server.server import create_app
from src.utils import get_logger, init_logging_from_env

init_logging_from_env()
logger = get_logger(__name__)


class ServerManager:
    """Управляет запуском, остановкой и получением кода с сервера."""

    def __init__(self, settings: CallbackServerSettings):
        self._settings = settings
        self._code_handler = CodeFileHandler()
        self._shutdown_event = asyncio.Event()

    async def run_and_wait_for_code(self) -> str:
        """
        Запускает сервер и ждет получения кода авторизации.

        Returns:
            Код авторизации.
        """
        self._code_handler.cleanup()

        config = uvicorn.Config(
            create_app(self._shutdown_event),
            host=self._settings.host,
            port=self._settings.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)

        server_task = asyncio.create_task(server.serve())
        await self._shutdown_event.wait()
        server.should_exit = True
        await server_task

        try:
            code = self._code_handler.read()
            return code
        except FileNotFoundError:
            logger.error("Сервер был остановлен, но код авторизации не был получен.")
            sys.exit(1)
        finally:
            self._code_handler.cleanup()