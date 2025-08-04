# src/hh_adapter/client.py
# --- agent_meta ---
# role: hh-api-client
# owner: @backend
# contract: Implements the client for interacting with the HH.ru API.
# last_reviewed: 2025-07-24
# interfaces:
#   - HHApiClient.request(endpoint: str, method: str, data: Optional[Dict], params: Optional[Dict]) -> Dict[str, Any]
# --- /agent_meta ---

from typing import Any, Dict, Optional

import aiohttp

from aiohttp import ClientError

from .config import HHSettings
from .tokens import HHTokenManager, HHTokenError
from src.utils import get_logger

logger = get_logger(__name__)


class HHApiError(Exception):
    """Базовое исключение для ошибок API клиента."""
    pass

class HHApiClient:
    """Клиент для работы с API HeadHunter."""

    def __init__(self, settings: HHSettings, token_manager: HHTokenManager, session: aiohttp.ClientSession):
        """
        Инициализация клиента API.

        Args:
            settings: Настройки для сервиса HH.ru.
            token_manager: Менеджер токенов.
            session: Сессия aiohttp.
        """
        self._settings = settings
        self._token_manager = token_manager
        self._session = session

    async def request(
        self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Выполнение запроса к API с автоматическим обновлением токена.

        Args:
            endpoint: Эндпоинт API.
            method: HTTP метод.
            data: Тело запроса.
            params: Параметры запроса.

        Returns:
            Ответ от API в виде словаря.
        """
        try:
            # Перед каждым запросом получаем действительный токен.
            # Менеджер токенов сам позаботится о его обновлении, если нужно.
            access_token = await self._token_manager.get_valid_access_token()
        except HHTokenError as e:
            raise HHApiError(f"Ошибка получения токена доступа: {e}") from e

        # Формируем стандартные заголовки для запроса к API HH.ru.
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'ResumeBot/1.0'
        }
        url = f'{self._settings.base_url}{endpoint}'

        try:
            async with self._session.request(method, url, headers=headers, params=params, json=data) as response:
                response.raise_for_status()
                # Некоторые запросы (например, DELETE) могут возвращать пустой ответ
                # со статусом 204, который нельзя парсить как JSON.
                if response.status == 204:  # No Content
                    return {}
                return await response.json()
        except ClientError as e:
            logger.error(f"Ошибка при запросе к API {url}: {e}")
            raise HHApiError(f"Ошибка API: {e}") from e
