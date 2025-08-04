# src/hh_adapter/tokens.py
# --- agent_meta ---
# role: hh-token-manager
# owner: @backend
# contract: Manages the lifecycle of HH.ru API tokens.
# last_reviewed: 2025-07-24
# interfaces:
#   - HHTokenManager.exchange_code(code: str) -> None
#   - HHTokenManager.get_valid_access_token() -> str
# --- /agent_meta ---

import time
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientError

from .config import HHSettings
from src.utils import get_logger

logger = get_logger(__name__)

class HHTokenError(Exception):
    """Базовое исключение для ошибок, связанных с токенами."""
    pass


class HHTokenManager:
    """Менеджер для управления токенами доступа HH.ru."""

    def __init__(
        self, settings: HHSettings, session: aiohttp.ClientSession, access_token: Optional[str] = None, refresh_token: Optional[str] = None, expires_in: int = 0
    ):
        """
        Инициализация менеджера токенов.

        Args:
            settings: Настройки для сервиса HH.ru.
            session: Сессия aiohttp.
            access_token: Токен доступа.
            refresh_token: Токен обновления.
            expires_in: Время жизни токена в секундах.
        """
        self._settings = settings
        self._session = session
        self.access_token = access_token
        self.refresh_token = refresh_token
        # Сразу вычисляем абсолютное время истечения токена для удобства.
        self.expires_at = time.time() + expires_in

    async def exchange_code(self, code: str) -> None:
        """
        Обмен кода авторизации на токены доступа.

        Args:
            code: Код авторизации.
        """
        # Для первичного получения токенов HH.ru требует grant_type 'authorization_code'.
        payload = {
            'grant_type': 'authorization_code',
            'client_id': self._settings.client_id,
            'client_secret': self._settings.client_secret,
            'code': code,
            'redirect_uri': self._settings.redirect_uri
        }
        headers = {
            # User-Agent обязателен для всех запросов к API HH.ru.
            "User-Agent": "ResumeBot/1.0",
        }
        try:
            async with self._session.post(self._settings.token_url, data=payload, headers=headers) as response:
                response.raise_for_status()
                tokens = await response.json()
                self._update_tokens(tokens)
        except ClientError as e:
            logger.error(f"Ошибка при обмене кода на токен: {e}")
            raise HHTokenError(f"Не удалось обменять код на токен: {e}") from e

    async def get_valid_access_token(self) -> str:
        """
        Получение действительного токена, при необходимости с обновлением.

        Returns:
            Действительный токен доступа.
        """
        # Обновляем токен превентивно, за 5 минут до истечения срока,
        # чтобы избежать гонки состояний и ошибок при реальных запросах.
        if not self.access_token or time.time() + 300 >= self.expires_at:
            await self._refresh_token()
        
        if not self.access_token:
            # Если токен так и не появился, значит, произошла ошибка.
            raise HHTokenError("Отсутствует access_token после попытки обновления.")

        return self.access_token

    async def _refresh_token(self) -> None:
        """Обновление токена доступа."""
        if not self.refresh_token:
            # Если refresh_token отсутствует, мы не можем обновить access_token
            # и должны будем заново проходить процесс авторизации.
            raise HHTokenError("Отсутствует refresh_token для обновления.")

        # Для обновления токена используется grant_type 'refresh_token'.
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }

        try:
            async with self._session.post(self._settings.token_url, data=payload) as response:
                response.raise_for_status()
                tokens = await response.json()
                self._update_tokens(tokens)
        except ClientError as e:
            logger.error(f"Ошибка при обновлении токена: {e}")
            raise HHTokenError(f"Не удалось обновить токен: {e}") from e

    def _update_tokens(self, tokens: Dict[str, Any]) -> None:
        """
        Обновляет токены и время их истечения.

        Args:
            tokens: Словарь с токенами.
        """
        self.access_token = tokens['access_token']
        # При обновлении токена HH.ru может не вернуть новый refresh_token.
        # В таком случае стандарт OAuth2 предписывает использовать старый.
        self.refresh_token = tokens.get('refresh_token', self.refresh_token)
        self.expires_at = time.time() + tokens['expires_in']
