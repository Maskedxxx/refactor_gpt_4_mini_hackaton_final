# src/callback_server/manager.py
# --- agent_meta ---
# role: oauth2-callback-server-manager
# owner: @backend
# contract: Управляет жизненным циклом callback сервера для OAuth2 авторизации
# last_reviewed: 2025-08-04
# interfaces:
#   - ServerManager.run_and_wait_for_code() -> str
# dependencies:
#   - CallbackServerSettings
#   - CodeFileHandler
#   - uvicorn.Server
# patterns: Facade Pattern, Server Lifecycle Management
# --- /agent_meta ---

import asyncio
import sys

import uvicorn

from src.callback_server.code_handler import CodeFileHandler
from src.callback_server.config import CallbackServerSettings
from src.callback_server.server import create_app
from src.utils import get_logger, init_logging_from_env

init_logging_from_env()
logger = get_logger(__name__)


class ServerManager:
    """Менеджер жизненного цикла callback сервера для OAuth2 авторизации.
    
    Этот класс реализует архитектурный паттерн "Facade" для управления callback сервером,
    который используется в OAuth2 Authorization Code Flow. Сервер временно запускается
    для получения кода авторизации от OAuth2 провайдера и автоматически завершает работу
    после успешного получения кода.
    
    Архитектурные принципы:
    - Single Responsibility: отвечает только за управление жизненным циклом сервера
    - Dependency Injection: принимает настройки через конструктор
    - Clean Shutdown: корректно завершает работу сервера и очищает ресурсы
    - Error Handling: обрабатывает ошибки и логирует все операции
    
    Интеграция с OAuth2 flow:
    1. Клиентское приложение перенаправляет пользователя на OAuth2 провайдер
    2. После авторизации провайдер делает callback на локальный сервер
    3. Сервер получает код авторизации и сохраняет его через CodeFileHandler
    4. Сервер автоматически завершает работу и возвращает код клиенту
    
    Пример использования:
        >>> settings = CallbackServerSettings(host="127.0.0.1", port=8080)
        >>> manager = ServerManager(settings)
        >>> auth_code = await manager.run_and_wait_for_code()
        >>> print(f"Получен код: {auth_code}")
    
    Args:
        settings: Настройки сервера (хост, порт)
        
    Attributes:
        _settings: Конфигурация сервера
        _code_handler: Обработчик для работы с файлом кода авторизации
        _shutdown_event: Событие для координации завершения работы сервера
    """

    def __init__(self, settings: CallbackServerSettings) -> None:
        self._settings = settings
        self._code_handler = CodeFileHandler()
        self._shutdown_event = asyncio.Event()
        logger.debug("ServerManager инициализирован для %s:%d", settings.host, settings.port)

    async def run_and_wait_for_code(self) -> str:
        """Запускает callback сервер и асинхронно ожидает получения кода авторизации.
        
        Метод реализует полный цикл работы с OAuth2 callback:
        1. Очищает предыдущие временные файлы с кодами
        2. Создает и настраивает uvicorn сервер с FastAPI приложением
        3. Запускает сервер в отдельной задаче
        4. Ожидает получения кода через shutdown_event
        5. Корректно останавливает сервер
        6. Читает полученный код из временного файла
        7. Очищает временные файлы
        
        Архитектурные особенности:
        - Использует асинхронное программирование для неблокирующего ожидания
        - Применяет паттерн "Event-driven" через asyncio.Event
        - Обеспечивает graceful shutdown сервера
        - Гарантирует очистку ресурсов в блоке finally
        
        Пример OAuth2 flow:
            # 1. Запуск сервера
            manager = ServerManager(settings)
            
            # 2. Пользователь переходит по ссылке авторизации
            auth_url = "https://oauth.provider.com/authorize?..."
            webbrowser.open(auth_url)
            
            # 3. Ожидание callback с кодом
            code = await manager.run_and_wait_for_code()
            
            # 4. Обмен кода на токены
            tokens = await exchange_code_for_tokens(code)
        
        Returns:
            str: Код авторизации, полученный от OAuth2 провайдера.
            
        Raises:
            SystemExit: Если код не был получен (сервер завершился без callback).
            IOError: При ошибках работы с временными файлами.
            
        Note:
            Метод блокирует выполнение до получения кода или ошибки.
            Для отмены операции можно использовать asyncio.timeout() или
            asyncio.wait_for() с таймаутом.
        """
        logger.info("Запуск callback сервера для получения кода авторизации")
        logger.debug("Очистка предыдущих файлов с кодом авторизации")
        self._code_handler.cleanup()

        config = uvicorn.Config(
            create_app(self._shutdown_event),
            host=self._settings.host,
            port=self._settings.port,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        
        logger.info("Сервер запускается на %s:%d", self._settings.host, self._settings.port)
        server_task = asyncio.create_task(server.serve())
        
        logger.info("Ожидание получения кода авторизации...")
        await self._shutdown_event.wait()
        
        logger.info("Получен сигнал завершения, останавливаем сервер")
        server.should_exit = True
        await server_task
        logger.debug("Сервер успешно остановлен")

        try:
            code = self._code_handler.read()
            logger.info("Код авторизации успешно получен: %s...", code[:8] if code else "None")
            return code
        except FileNotFoundError:
            logger.error("Сервер был остановлен, но код авторизации не был получен")
            sys.exit(1)
        finally:
            logger.debug("Очистка временных файлов")
            self._code_handler.cleanup()