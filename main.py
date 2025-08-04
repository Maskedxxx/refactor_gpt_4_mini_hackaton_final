# main.py

import asyncio

from src.utils import get_logger, init_logging_from_env

init_logging_from_env()
logger = get_logger(__name__)


async def main():
    """Основная точка входа для всего приложения."""
    logger.info("Приложение запущено.")
    # TODO: Здесь будет основная логика приложения
    await asyncio.sleep(1)  # Пример асинхронной операции
    logger.info("Приложение завершило работу.")


if __name__ == "__main__":
    asyncio.run(main())