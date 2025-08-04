# src/utils.py
# --- agent_meta ---
# role: utility-functions
# owner: @backend
# contract: Provides common utility functions like logging setup.
# last_reviewed: 2025-07-24
# interfaces:
#   - init_logging_from_env()
#   - get_logger()
# --- /agent_meta ---

import logging
import os

def init_logging_from_env():
    """Инициализирует конфигурацию логирования на основе переменных окружения."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def get_logger(name: str = "app") -> logging.Logger:
    """Возвращает инстанс логгера."""
    return logging.getLogger(name)
