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
    """
    Исключение для ошибок при взаимодействии с API HeadHunter.
    
    Возникает при HTTP ошибках, проблемах сети, некорректных ответах API
    или других проблемах взаимодействия с внешним сервисом. Оборачивает
    исходные исключения для удобства обработки на верхних уровнях.
    """
    pass

class HHApiClient:
    """
    HTTP клиент для взаимодействия с REST API HeadHunter.
    
    Предоставляет высокоуровневый интерфейс для выполнения аутентифицированных
    запросов к API HH.ru. Автоматически управляет токенами доступа через 
    интеграцию с HHTokenManager, обеспечивая бесшовную работу приложения.
    
    Основные возможности:
    - Автоматическая аутентификация всех запросов
    - Прозрачное обновление истекших токенов
    - Обработка различных HTTP методов (GET, POST, PUT, DELETE)
    - Автоматическая сериализация/десериализация JSON
    - Комплексная обработка ошибок и логирование
    
    Attributes:
        _settings: Конфигурация API (base_url, endpoints)
        _token_manager: Менеджер OAuth2 токенов  
        _session: Переиспользуемая HTTP сессия aiohttp
    """

    def __init__(self, settings: HHSettings, token_manager: HHTokenManager, session: aiohttp.ClientSession):
        """
        Инициализация HTTP клиента для API HeadHunter.

        Args:
            settings: Конфигурация подключения к API HH.ru, включая base_url
                     и другие параметры. Обычно загружается из переменных окружения.
            token_manager: Экземпляр HHTokenManager для управления OAuth2 токенами.
                          Должен быть предварительно инициализирован с валидными токенами.
            session: Переиспользуемая aiohttp сессия для выполнения HTTP запросов.
                    Рекомендуется использовать один экземпляр для всего приложения.
                    
        Example:
            >>> settings = HHSettings()
            >>> token_manager = HHTokenManager(settings, session)
            >>> await token_manager.exchange_code("auth_code_from_oauth")
            >>> 
            >>> api_client = HHApiClient(settings, token_manager, session)
            >>> user_info = await api_client.request("me")
        """
        self._settings = settings
        self._token_manager = token_manager
        self._session = session
        logger.debug("HHApiClient инициализирован для base_url: %s", settings.base_url)

    async def request(
        self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Выполняет аутентифицированный HTTP запрос к API HeadHunter.
        
        Автоматически добавляет необходимые заголовки (Authorization, User-Agent),
        получает валидный токен доступа и обрабатывает ответы API. При необходимости
        прозрачно обновляет истекшие токены через HHTokenManager.

        Args:
            endpoint: Относительный путь к API эндпоинту (например, "me", "vacancies/search").
                     Будет добавлен к base_url из настроек.
            method: HTTP метод для запроса. Поддерживаются: GET, POST, PUT, DELETE, PATCH.
                   По умолчанию 'GET'.
            data: Данные для отправки в теле запроса (для POST/PUT). Автоматически 
                 сериализуются в JSON. Для GET запросов должно быть None.
            params: URL параметры запроса в виде словаря. Будут добавлены в query string.
                   Например: {"per_page": 50, "page": 1}

        Returns:
            Dict[str, Any]: Десериализованный JSON ответ от API в виде словаря.
                           Для запросов с статусом 204 (No Content) возвращается пустой словарь.

        Raises:
            HHApiError: При ошибках HTTP запроса, проблемах сети или некорректных ответах.
                       Оборачивает исходные aiohttp.ClientError для удобства обработки.
            HHTokenError: При проблемах получения или обновления токенов доступа.
                         Передается как HHApiError с дополнительным контекстом.
                         
        Example:
            >>> # Получение информации о текущем пользователе
            >>> user_info = await client.request("me")
            >>> print(user_info["first_name"])
            
            >>> # Поиск вакансий с параметрами
            >>> vacancies = await client.request("vacancies", params={"text": "Python", "per_page": 10})
            >>> 
            >>> # Создание резюме (POST запрос)
            >>> resume_data = {"title": "Python Developer", "skills": ["Python", "Django"]}
            >>> new_resume = await client.request("resumes", method="POST", data=resume_data)
        """
        url = f'{self._settings.base_url}{endpoint}'
        logger.info("Выполняется запрос к API: %s %s", method, endpoint)
        logger.debug("Полный URL: %s, params: %s, data: %s", url, params, "[присутствует]" if data else None)
        
        try:
            # Перед каждым запросом получаем действительный токен.
            # Менеджер токенов сам позаботится о его обновлении, если нужно.
            access_token = await self._token_manager.get_valid_access_token()
        except HHTokenError as e:
            logger.error("Ошибка получения токена доступа: %s", e)
            raise HHApiError(f"Ошибка получения токена доступа: {e}") from e

        # Формируем стандартные заголовки для запроса к API HH.ru.
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'ResumeBot/1.0'
        }

        try:
            async with self._session.request(method, url, headers=headers, params=params, json=data) as response:
                logger.debug("Получен ответ: status=%d, content-type=%s", 
                           response.status, response.headers.get('content-type', 'unknown'))
                response.raise_for_status()
                
                # Некоторые запросы (например, DELETE) могут возвращать пустой ответ
                # со статусом 204, который нельзя парсить как JSON.
                if response.status == 204:  # No Content
                    logger.debug("Получен ответ без содержимого (204)")
                    return {}
                    
                result = await response.json()
                logger.info("Запрос к API успешно выполнен: %s %s", method, endpoint)
                return result
                
        except ClientError as e:
            logger.error("Ошибка при запросе к API %s: %s", url, e)
            raise HHApiError(f"Ошибка API: {e}") from e
