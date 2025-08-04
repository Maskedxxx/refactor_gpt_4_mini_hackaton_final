# src/hh_adapter/tokens.py
# --- agent_meta ---
# role: hh-oauth2-token-manager
# owner: @backend
# contract: Управляет жизненным циклом OAuth2 токенов HH.ru с автоматическим обновлением
# last_reviewed: 2025-08-04
# interfaces:
#   - HHTokenManager.exchange_code(code: str) -> None
#   - HHTokenManager.get_valid_access_token() -> str
# dependencies:
#   - HHSettings
#   - aiohttp.ClientSession
# patterns: Token Manager, Automatic Refresh, OAuth2 RFC 6749
# --- /agent_meta ---

import time
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientError

from .config import HHSettings
from src.utils import get_logger

logger = get_logger(__name__)

class HHTokenError(Exception):
    """
    Исключение для ошибок операций с OAuth2 токенами.
    
    Возникает при проблемах с получением, обновлением или валидацией
    токенов доступа к API HeadHunter. Включает как сетевые ошибки,
    так и ошибки OAuth2 протокола.
    """
    pass


class HHTokenManager:
    """
    Менеджер жизненного цикла OAuth2 токенов для API HeadHunter.
    
    Автоматически управляет получением, хранением и обновлением токенов доступа.
    Реализует превентивное обновление токенов (за 5 минут до истечения) для
    избежания прерываний в работе API. Следует OAuth2 RFC 6749 спецификации.
    
    Основные функции:
    - Обмен authorization_code на access/refresh токены
    - Автоматическое обновление истекающих токенов  
    - Безопасное хранение состояния токенов в памяти
    - Обработка ошибок OAuth2 протокола
    
    Attributes:
        access_token: Текущий токен доступа к API
        refresh_token: Токен для обновления access_token
        expires_at: Unix timestamp истечения access_token
    """

    def __init__(
        self, settings: HHSettings, session: aiohttp.ClientSession, access_token: Optional[str] = None, refresh_token: Optional[str] = None, expires_in: int = 0
    ):
        """
        Инициализация менеджера токенов для работы с API HeadHunter.
        
        Создает экземпляр менеджера для управления OAuth2 токенами. При наличии
        существующих токенов автоматически рассчитывает время их истечения.
        Поддерживает как создание "чистого" менеджера для первичной авторизации,
        так и восстановление состояния с существующими токенами.

        Args:
            settings (HHSettings): Конфигурационные настройки для интеграции с HH.ru API.
                Должен содержать client_id, client_secret, redirect_uri и token_url.
            session (aiohttp.ClientSession): HTTP-сессия для выполнения запросов к API.
                Рекомендуется использовать одну сессию для всех запросов.
            access_token (Optional[str], optional): Существующий токен доступа к API.
                Если не указан, потребуется выполнить exchange_code(). По умолчанию None.
            refresh_token (Optional[str], optional): Токен для обновления access_token.
                Необходим для автоматического обновления истекших токенов. По умолчанию None.
            expires_in (int, optional): Время жизни access_token в секундах от текущего момента.
                Используется для расчета expires_at. По умолчанию 0 (токен считается истекшим).
                
        Examples:
            Создание нового менеджера для первичной авторизации:
            
            >>> settings = HHSettings(client_id="...", client_secret="...")
            >>> async with aiohttp.ClientSession() as session:
            ...     manager = HHTokenManager(settings, session)
            ...     await manager.exchange_code("auth_code_from_callback")
            
            Восстановление менеджера с существующими токенами:
            
            >>> manager = HHTokenManager(
            ...     settings=settings,
            ...     session=session,
            ...     access_token="existing_access_token",
            ...     refresh_token="existing_refresh_token", 
            ...     expires_in=3600  # токен истекает через час
            ... )
            
        Note:
            После инициализации expires_at рассчитывается как текущее время + expires_in.
            Это позволяет менеджеру корректно определять необходимость обновления токена.
        """
        self._settings = settings
        self._session = session
        self.access_token = access_token
        self.refresh_token = refresh_token
        # Сразу вычисляем абсолютное время истечения токена для удобства.
        self.expires_at = time.time() + expires_in
        
        token_status = "с токенами" if access_token else "без токенов"
        logger.debug("HHTokenManager инициализирован %s", token_status)

    async def exchange_code(self, code: str) -> None:
        """
        Выполняет обмен кода авторизации на пару токенов доступа по OAuth2 протоколу.
        
        Реализует первый этап OAuth2 Authorization Code Grant Flow. Отправляет код авторизации,
        полученный после перенаправления пользователя с /oauth/authorize, на эндпоинт /oauth/token
        для получения access_token и refresh_token. После успешного обмена автоматически
        обновляет внутреннее состояние менеджера.
        
        OAuth2 Flow:
        1. Пользователь переходит по ссылке авторизации
        2. HH.ru перенаправляет на redirect_uri с параметром code
        3. Этот метод обменивает code на токены
        4. Полученные токены сохраняются для дальнейшего использования

        Args:
            code (str): Код авторизации, полученный от HH.ru после успешной авторизации
                пользователя. Обычно передается как GET-параметр 'code' в callback URL.
                Код имеет ограниченное время жизни (обычно 10 минут) и может быть
                использован только один раз.
                
        Raises:
            HHTokenError: Возникает при ошибках во время обмена кода на токены.
                Основные причины:
                - Недействительный или истекший код авторизации
                - Неверные client_id/client_secret в настройках
                - Несоответствие redirect_uri тому, что указан в приложении
                - Сетевые ошибки при запросе к API HH.ru
                - Проблемы на стороне сервера HH.ru (5xx ошибки)
                
        Examples:
            Обмен кода после редиректа пользователя:
            
            >>> # Пользователь авторизовался и вернулся с кодом
            >>> authorization_code = "received_from_callback_url"
            >>> try:
            ...     await token_manager.exchange_code(authorization_code)
            ...     print("Токены успешно получены")
            ... except HHTokenError as e:
            ...     print(f"Ошибка авторизации: {e}")
                
        Note:
            После успешного выполнения метода access_token, refresh_token и expires_at
            будут автоматически обновлены. Код может быть использован только один раз,
            повторный вызов с тем же кодом вызовет ошибку.
        """
        logger.info("Начинается обмен кода авторизации на токены")
        logger.debug("Код авторизации: %s...", code[:8] if code else "None")
        
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
                logger.info("Токены успешно получены и обновлены")
        except ClientError as e:
            logger.error("Ошибка при обмене кода на токен: %s", e)
            raise HHTokenError(f"Не удалось обменять код на токен: {e}") from e

    async def get_valid_access_token(self) -> str:
        """
        Возвращает действительный токен доступа с автоматическим обновлением при необходимости.
        
        Главный метод для получения токена доступа в приложении. Автоматически проверяет
        срок действия текущего токена и обновляет его превентивно (за 5 минут до истечения)
        для предотвращения прерываний в работе API. Гарантирует, что возвращаемый токен
        будет действителен минимум 5 минут.
        
        Логика работы:
        1. Проверяет наличие access_token
        2. Если токен отсутствует или истекает в течение 5 минут - обновляет его
        3. Возвращает гарантированно действительный токен
        
        Превентивное обновление за 5 минут необходимо для:
        - Избежания ситуаций, когда токен истекает во время выполнения запроса
        - Предотвращения гонок состояний в многопоточной среде
        - Обеспечения стабильной работы долгоживущих операций

        Returns:
            str: Действительный токен доступа, готовый для использования в Authorization header.
                Формат: "Bearer {access_token}" не добавляется автоматически.
                
        Raises:
            HHTokenError: Возникает в следующих случаях:
                - Отсутствует refresh_token для обновления истекшего access_token
                - Ошибка при обновлении токена (сетевые проблемы, невалидный refresh_token)
                - После попытки обновления access_token все еще отсутствует
                - Проблемы аутентификации с HH.ru API
                
        Examples:
            Получение токена для API запроса:
            
            >>> try:
            ...     token = await token_manager.get_valid_access_token()
            ...     headers = {"Authorization": f"Bearer {token}"}
            ...     # Выполняем запрос к HH.ru API
            ...     async with session.get("https://api.hh.ru/me", headers=headers) as resp:
            ...         user_info = await resp.json()
            ... except HHTokenError as e:
            ...     print(f"Не удалось получить токен: {e}")
            ...     # Возможно, нужна повторная авторизация пользователя
                
            Использование в middleware или декораторе:
            
            >>> async def api_request_with_auth(url: str) -> dict:
            ...     token = await token_manager.get_valid_access_token()
            ...     headers = {"Authorization": f"Bearer {token}"}
            ...     async with session.get(url, headers=headers) as response:
            ...         return await response.json()
                
        Note:
            Метод является async и может выполнять сетевые запросы для обновления токена.
            Рекомендуется кэшировать результат на короткое время (1-2 минуты) если метод
            вызывается очень часто, но не дольше 5 минут из-за превентивного обновления.
        """
        # Обновляем токен превентивно, за 5 минут до истечения срока,
        # чтобы избежать гонки состояний и ошибок при реальных запросах.
        current_time = time.time()
        expires_soon = current_time + 300 >= self.expires_at
        
        if not self.access_token:
            logger.debug("Токен доступа отсутствует, требуется обновление")
        elif expires_soon:
            logger.debug("Токен доступа истекает в течение 5 минут, требуется обновление")
            
        if not self.access_token or expires_soon:
            await self._refresh_token()
        
        if not self.access_token:
            # Если токен так и не появился, значит, произошла ошибка.
            logger.error("Отсутствует access_token после попытки обновления")
            raise HHTokenError("Отсутствует access_token после попытки обновления.")

        logger.debug("Возвращается действительный токен доступа")
        return self.access_token

    async def _refresh_token(self) -> None:
        """
        Внутренний метод для обновления истекшего или истекающего токена доступа.
        
        Использует refresh_token для получения нового access_token по OAuth2 протоколу.
        Выполняет запрос к эндпоинту /oauth/token с grant_type='refresh_token'.
        При успешном обновлении автоматически обновляет внутреннее состояние менеджера
        через _update_tokens().
        
        Логика обновления:
        1. Проверяет наличие refresh_token
        2. Формирует запрос с grant_type='refresh_token'
        3. Отправляет запрос к HH.ru token endpoint
        4. Обновляет токены в памяти
        
        В соответствии с RFC 6749, при обновлении токена сервер может:
        - Вернуть новый refresh_token (рекомендуется для безопасности)
        - Не вернуть refresh_token (тогда используется существующий)
        
        Raises:
            HHTokenError: Возникает в следующих ситуациях:
                - Отсутствует refresh_token (требуется повторная авторизация)
                - Refresh_token недействителен или истек
                - Сетевые ошибки при запросе к API
                - Ошибки аутентификации приложения (неверный client_id/secret)
                - Серверные ошибки на стороне HH.ru
                
        Note:
            Это внутренний метод, не предназначенный для прямого вызова.
            Используйте get_valid_access_token() для получения действительных токенов.
            
            Метод не выполняет дополнительных проверок времени истечения -
            эта логика реализована в get_valid_access_token().
            
            При ошибке обновления состояние менеджера не изменяется,
            старые токены остаются неизменными до успешного обновления.
        """
        logger.info("Начинается обновление токена доступа")
        
        if not self.refresh_token:
            # Если refresh_token отсутствует, мы не можем обновить access_token
            # и должны будем заново проходить процесс авторизации.
            logger.error("Отсутствует refresh_token для обновления")
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
                logger.info("Токен доступа успешно обновлен")
        except ClientError as e:
            logger.error("Ошибка при обновлении токена: %s", e)
            raise HHTokenError(f"Не удалось обновить токен: {e}") from e

    def _update_tokens(self, tokens: Dict[str, Any]) -> None:
        """
        Внутренний метод для обновления состояния токенов в памяти.
        
        Принимает ответ от HH.ru OAuth2 эндпоинта и обновляет внутреннее состояние
        менеджера. Корректно обрабатывает как первичное получение токенов
        (exchange_code), так и их обновление (_refresh_token).
        
        Обрабатываемые поля ответа:
        - access_token: новый токен доступа (всегда присутствует)
        - refresh_token: новый токен обновления (опционально при refresh)
        - expires_in: время жизни access_token в секундах
        
        Особенности обработки:
        - expires_at рассчитывается как текущее время + expires_in
        - Если refresh_token отсутствует в ответе, сохраняется старый
        - Логирует информацию об обновлении для отладки

        Args:
            tokens (Dict[str, Any]): Словарь с данными токенов от HH.ru API.
                Ожидаемая структура:
                {
                    "access_token": "новый_токен_доступа",
                    "refresh_token": "новый_refresh_token",  # опционально
                    "expires_in": 86400,  # время жизни в секундах
                    "token_type": "bearer"  # игнорируется
                }
                
        Examples:
            Обработка ответа от exchange_code:
            
            >>> response_data = {
            ...     "access_token": "new_access_token_here",
            ...     "refresh_token": "new_refresh_token_here",
            ...     "expires_in": 86400,
            ...     "token_type": "bearer"
            ... }
            >>> manager._update_tokens(response_data)
            
            Обработка ответа от refresh (без нового refresh_token):
            
            >>> refresh_response = {
            ...     "access_token": "updated_access_token",
            ...     "expires_in": 86400
            ...     # refresh_token отсутствует - используется существующий
            ... }
            >>> manager._update_tokens(refresh_response)
                
        Note:
            Это внутренний метод, вызываемый только из exchange_code() и _refresh_token().
            Не выполняет валидацию входных данных - предполагается корректный ответ от API.
            
            Время expires_at рассчитывается в момент обновления, поэтому небольшие
            задержки сети учитываются автоматически (токен "стареет" с момента получения).
        """
        old_token_present = bool(self.access_token)
        
        self.access_token = tokens['access_token']
        # При обновлении токена HH.ru может не вернуть новый refresh_token.
        # В таком случае стандарт OAuth2 предписывает использовать старый.
        self.refresh_token = tokens.get('refresh_token', self.refresh_token)
        self.expires_at = time.time() + tokens['expires_in']
        
        logger.debug("Токены обновлены: access_token=%s, refresh_token=%s, expires_in=%ds", 
                    "обновлен" if old_token_present else "получен",
                    "обновлен" if tokens.get('refresh_token') else "сохранен старый",
                    tokens['expires_in'])
