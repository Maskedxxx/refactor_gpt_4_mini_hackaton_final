# src/config.py
# --- agent_meta ---
# role: application-settings-model
# owner: @backend
# contract: Defines the main application settings model.
# last_reviewed: 2025-07-24
# interfaces:
#   - AppSettings
# --- /agent_meta ---

from pydantic import Field
from pydantic_settings import BaseSettings

from src.callback_server.config import CallbackServerSettings
from src.hh_adapter.config import HHSettings


class AppSettings(BaseSettings):
    """
    Главный класс конфигурации приложения.
    
    Собирает все настройки из переменных окружения и дочерних моделей.
    """
    hh: HHSettings = Field(default_factory=HHSettings)
    callback_server: CallbackServerSettings = Field(default_factory=CallbackServerSettings)