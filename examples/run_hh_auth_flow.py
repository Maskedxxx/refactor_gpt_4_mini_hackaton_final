# examples/run_hh_auth_flow.py

# --- agent_meta ---
# role: integration-example
# owner: @backend
# contract: Demonstrates the end-to-end OAuth2 flow by orchestrating callback_server and hh_adapter.
# last_reviewed: 2025-08-05
# dependencies: [aiohttp, src.config, src.hh_adapter, src.callback_server]
# --- /agent_meta ---

import asyncio
import webbrowser

import aiohttp

from src.callback_server.manager import ServerManager
from src.config import AppSettings
from src.hh_adapter.auth import HHAuthService
from src.hh_adapter.client import HHApiClient
from src.hh_adapter.tokens import HHTokenManager
from src.utils import get_logger, init_logging_from_env

init_logging_from_env()
logger = get_logger(__name__)


# --- Флаг для использования мокового (тестового) кода авторизации ---
# Установите True, чтобы пропустить реальную авторизацию через браузер
# и использовать тестовый код.
USE_MOCK_AUTH = False
MOCK_AUTH_CODE = "mock_code_from_script"  # Тестовый код
# --------------------------------------------------------------------


async def main():
    """Основная функция приложения."""
    # 1. Инициализация
    settings = AppSettings()
    auth_service = HHAuthService(settings.hh)
    auth_code: str

    # 2. Получение кода авторизации
    if USE_MOCK_AUTH:
        logger.info("Используется моковый код авторизации.")
        auth_code = MOCK_AUTH_CODE
    else:
        auth_url = auth_service.get_auth_url()
        logger.info(f"Откройте эту ссылку в браузере для авторизации: {auth_url}")
        webbrowser.open(auth_url)

        server_manager = ServerManager(settings.callback_server)
        auth_code = await server_manager.run_and_wait_for_code()
    
    logger.info(f"Код авторизации успешно получен: {auth_code}")

    # 3. Обмен кода на токены и работа с API
    async with aiohttp.ClientSession() as session:
        token_manager = HHTokenManager(settings.hh, session)
        await token_manager.exchange_code(auth_code)
        logger.info("Токены успешно получены.")

        # 4. Пример запроса к API
        api_client = HHApiClient(settings.hh, token_manager, session)
        try:
            # Пример: получение информации о текущем пользователе
            user_info = await api_client.request("me")
            logger.info(f"Информация о пользователе: {user_info}")
        except Exception as e:
            logger.error(f"Ошибка при запросе к API: {e}")


if __name__ == "__main__":
    asyncio.run(main())
