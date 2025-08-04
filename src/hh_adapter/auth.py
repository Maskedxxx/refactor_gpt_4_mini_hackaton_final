# src/hh_adapter/auth.py
# --- agent_meta ---
# role: hh-auth-service
# owner: @backend
# contract: Provides HH.ru authorization URL.
# last_reviewed: 2025-07-24
# interfaces:
#   - HHAuthService.get_auth_url() -> str
# --- /agent_meta ---

from src.utils import get_logger
from .config import HHSettings

logger = get_logger(__name__)


class HHAuthService:
    """
    Сервис для работы с OAuth2 авторизацией HeadHunter.
    
    Отвечает за генерацию URL для инициации процесса авторизации пользователя
    через OAuth2 Authorization Code flow. Следует принципу единственной 
    ответственности (SRP) - только формирование URL авторизации.
    
    Attributes:
        _settings: Настройки подключения к API HH.ru (client_id, redirect_uri и др.)
    """

    def __init__(self, settings: HHSettings):
        """
        Инициализация сервиса авторизации.

        Args:
            settings: Экземпляр HHSettings с конфигурацией OAuth2 клиента.
                     Должен содержать client_id и redirect_uri.
                     
        Example:
            >>> settings = HHSettings(client_id="your_id", redirect_uri="http://localhost:8080/callback")
            >>> auth_service = HHAuthService(settings)
        """
        self._settings = settings
        logger.debug("HHAuthService инициализирован с client_id: %s", settings.client_id[:8] + "...")

    def get_auth_url(self) -> str:
        """
        Формирует URL для авторизации пользователя в системе HH.ru.
        
        Создает стандартный OAuth2 Authorization Code URL, который перенаправляет 
        пользователя на страницу авторизации HH.ru. После успешной авторизации
        пользователь будет перенаправлен на redirect_uri с кодом авторизации.

        Returns:
            str: Полный URL для авторизации, включающий параметры:
                - response_type=code (тип OAuth2 flow)
                - client_id (идентификатор OAuth2 приложения)  
                - redirect_uri (URL для возврата с кодом авторизации)
                
        Example:
            >>> auth_service = HHAuthService(settings)
            >>> url = auth_service.get_auth_url()
            >>> print(url)
            "https://hh.ru/oauth/authorize?response_type=code&client_id=***&redirect_uri=http://localhost:8080/callback"
        """
        logger.info("Генерируется URL авторизации для HH.ru")
        
        # Формируем стандартный OAuth2 Authorization Code URL согласно RFC 6749
        # Параметры URL строго соответствуют спецификации HH.ru API
        auth_url = (
            f'https://hh.ru/oauth/authorize?'
            f'response_type=code&'
            f'client_id={self._settings.client_id}&'
            f'redirect_uri={self._settings.redirect_uri}'
        )
        
        logger.debug("Сгенерирован URL авторизации: %s", auth_url.replace(self._settings.client_id, "***"))
        return auth_url
