# src/hh_adapter/config.py
# --- agent_meta ---
# role: hh-oauth2-settings-model
# owner: @backend
# contract: Модель конфигурации OAuth2 интеграции с API HH.ru
# last_reviewed: 2025-08-04
# interfaces:
#   - HHSettings
# dependencies:
#   - pydantic_settings.BaseSettings
# patterns: Configuration Object, Settings Pattern
# --- /agent_meta ---

from pydantic_settings import BaseSettings, SettingsConfigDict


class HHSettings(BaseSettings):
    """
    Модель конфигурации для OAuth2 интеграции с API HeadHunter.
    
    Содержит все необходимые настройки для подключения к API HH.ru через
    OAuth2 Authorization Code flow. Автоматически загружает конфигурацию
    из переменных окружения с префиксом HH_.
    
    Использует паттерн "Configuration Object" для централизованного управления
    настройками и валидации конфигурации через Pydantic.
    
    Attributes:
        client_id: Публичный идентификатор OAuth2 приложения, полученный при регистрации в HH.ru
        client_secret: Секретный ключ OAuth2 приложения для безопасной аутентификации
        redirect_uri: URL для перенаправления после авторизации (должен совпадать с зарегистрированным)
        base_url: Базовый URL для API запросов к HeadHunter (по умолчанию https://api.hh.ru/)
        token_url: URL эндпоинта для получения и обновления OAuth2 токенов
    
    Environment Variables:
        HH_CLIENT_ID: Идентификатор OAuth2 приложения
        HH_CLIENT_SECRET: Секретный ключ приложения  
        HH_REDIRECT_URI: URL для callback (например: http://localhost:8080/callback)
        HH_BASE_URL: Опционально, базовый URL API (по умолчанию https://api.hh.ru/)
        HH_TOKEN_URL: Опционально, URL токенов (по умолчанию https://hh.ru/oauth/token)
    
    Example:
        >>> # Автоматическая загрузка из .env файла
        >>> settings = HHSettings()
        >>> print(settings.client_id)  # Загружено из HH_CLIENT_ID
        >>> 
        >>> # Ручное создание для тестов
        >>> test_settings = HHSettings(
        ...     client_id="test_id",
        ...     client_secret="test_secret", 
        ...     redirect_uri="http://localhost:8080/callback"
        ... )
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
