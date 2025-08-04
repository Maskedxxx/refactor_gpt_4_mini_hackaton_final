# src/callback_server/config.py
# --- agent_meta ---
# role: callback-server-settings-model
# owner: @backend
# contract: Defines the settings structure for the callback server.
# last_reviewed: 2025-07-24
# interfaces:
#   - CallbackServerSettings
# --- /agent_meta ---

from pydantic_settings import BaseSettings, SettingsConfigDict


class CallbackServerSettings(BaseSettings):
    """
    Модель настроек для сервиса callback.
    """
    host: str = "127.0.0.1"
    port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix='CALLBACK_',
        extra='ignore'
    )