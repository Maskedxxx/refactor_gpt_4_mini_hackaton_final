# src/hh_adapter/auth.py
# --- agent_meta ---
# role: hh-auth-service
# owner: @backend
# contract: Provides HH.ru authorization URL.
# last_reviewed: 2025-07-24
# interfaces:
#   - HHAuthService.get_auth_url() -> str
# --- /agent_meta ---

from .config import HHSettings


class HHAuthService:
    """Сервис для работы с авторизацией в HH.ru."""

    def __init__(self, settings: HHSettings):
        """
        Инициализация сервиса авторизации.

        Args:
            settings: Настройки для сервиса HH.ru.
        """
        self._settings = settings

    def get_auth_url(self) -> str:
        """
        Генерация URL для авторизации пользователя.

        Returns:
            URL для авторизации.
        """
        # Формируем URL, на который нужно перенаправить пользователя
        # для получения кода авторизации (authorization code).
        return (
            f'https://hh.ru/oauth/authorize?'
            f'response_type=code&'
            f'client_id={self._settings.client_id}&'
            f'redirect_uri={self._settings.redirect_uri}'
        )
