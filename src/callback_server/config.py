# src/callback_server/config.py
# --- agent_meta ---
# role: oauth2-callback-server-settings
# owner: @backend
# contract: Модель конфигурации для OAuth2 callback сервера
# last_reviewed: 2025-08-04
# interfaces:
#   - CallbackServerSettings
# dependencies:
#   - pydantic_settings.BaseSettings
# patterns: Configuration Object, Settings Pattern
# --- /agent_meta ---

from pydantic_settings import BaseSettings, SettingsConfigDict


class CallbackServerSettings(BaseSettings):
    """
    Модель конфигурации для локального callback сервера OAuth2.
    
    Определяет настройки временного HTTP сервера, используемого для приема
    кода авторизации в рамках OAuth2 Authorization Code flow. Сервер запускается
    только на время получения callback'а и автоматически завершает работу.
    
    Использует паттерн "Configuration Object" для централизованного управления
    настройками сетевого подключения с автоматической загрузкой из переменных
    окружения через Pydantic Settings.
    
    Attributes:
        host: IP адрес для привязки HTTP сервера. По умолчанию "127.0.0.1" (localhost)
              для безопасности - сервер доступен только локально.
        port: TCP порт для прослушивания HTTP запросов. По умолчанию 8080.
              Должен совпадать с портом в redirect_uri OAuth2 приложения.
    
    Environment Variables:
        CALLBACK_HOST: IP адрес для bind (по умолчанию 127.0.0.1)
        CALLBACK_PORT: TCP порт для прослушивания (по умолчанию 8080)
    
    Security Notes:
        - Сервер привязывается только к localhost для безопасности
        - Используется только для получения одного callback запроса
        - Автоматически завершается после получения кода авторизации
        - Не должен быть доступен извне в продакшн среде
    
    Example:
        >>> # Автоматическая загрузка из .env файла
        >>> settings = CallbackServerSettings()
        >>> print(f"Сервер будет запущен на {settings.host}:{settings.port}")
        >>> 
        >>> # Ручное создание для тестов
        >>> test_settings = CallbackServerSettings(host="127.0.0.1", port=9000)
        >>> # Должно соответствовать: redirect_uri = "http://127.0.0.1:9000/callback"
    """
    host: str = "127.0.0.1"
    port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix='CALLBACK_',
        extra='ignore'
    )