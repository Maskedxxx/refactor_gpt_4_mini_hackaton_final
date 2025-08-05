# src/callback_server/__main__.py
# --- agent_meta ---
# role: component-demo-runner
# owner: @backend
# contract: Provides a CLI entry point to run the callback_server component independently for demonstration.
# last_reviewed: 2025-08-05
# dependencies: [asyncio, src.callback_server.manager, src.callback_server.config]
# --- /agent_meta ---

import asyncio
from src.callback_server.manager import ServerManager
from src.callback_server.config import CallbackServerSettings
from src.utils import get_logger

logger = get_logger(__name__)

async def main():
    """Запускает callback-сервер в демонстрационном режиме."""
    logger.info("Запуск callback-сервера в демонстрационном режиме...")
    
    try:
        settings = CallbackServerSettings()
        server_manager = ServerManager(settings)
        
        print(f"Сервер запущен и ожидает callback на http://{settings.host}:{settings.port}/callback")
        print("Чтобы протестировать, перейдите по ссылке, которая инициирует OAuth2 флоу.")
        print("После успешной авторизации вы будете перенаправлены на локальный сервер.")
        print("Нажмите Ctrl+C для отмены.")

        auth_code = await server_manager.run_and_wait_for_code()
        
        print("\n" + "="*50)
        logger.info("Сервер успешно получил код авторизации.")
        print(f"Полученный код: {auth_code}")
        print("="*50 + "\n")

    except asyncio.CancelledError:
        logger.warning("Запуск сервера отменен пользователем.")
    except Exception as e:
        logger.error(f"Произошла ошибка при работе сервера: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа завершена пользователем.")
