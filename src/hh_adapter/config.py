# src/hh_adapter/config.py
# --- agent_meta ---
# role: hh-adapter-settings-model
# owner: @backend
# contract: Defines the settings structure for the HH.ru adapter.
# last_reviewed: 2025-07-24
# interfaces:
#   - HHSettings
# --- /agent_meta ---

from pydantic_settings import BaseSettings, SettingsConfigDict


class HHSettings(BaseSettings):
    """
    Модель настроек для сервиса HH.ru.
    """
    client_id: str
    client_secret: str
    redirect_uri: str
    base_url: str = "https://api.hh.ru/"
    token_url: str = "https://hh.ru/oauth/token"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix='HH_',
        extra='ignore'
    )
