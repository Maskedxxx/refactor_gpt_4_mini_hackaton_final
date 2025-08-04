# src/callback_server/server.py
# --- agent_meta ---
# role: oauth2-callback-fastapi-app
# owner: @backend
# contract: FastAPI приложение для обработки OAuth2 callback запросов
# last_reviewed: 2025-08-04
# interfaces:
#   - create_app(shutdown_event: asyncio.Event) -> FastAPI
# dependencies:
#   - CodeFileHandler
#   - FastAPI
#   - asyncio.Event
# patterns: Factory Pattern, Event-driven Architecture
# --- /agent_meta ---

import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from src.callback_server.code_handler import CodeFileHandler
from src.utils import get_logger

logger = get_logger(__name__)

def create_app(shutdown_event: asyncio.Event) -> FastAPI:
    """Фабрика для создания FastAPI приложения с OAuth2 callback обработчиком.
    
    Эта функция реализует паттерн "Factory" для создания конфигурируемого 
    FastAPI приложения, которое обрабатывает OAuth2 Authorization Code 
    callback запросы. Приложение автоматически завершает работу 
    после успешного получения кода авторизации.
    
    Архитектурные принципы:
    - Factory Pattern: создает настроенное приложение по параметрам
    - Dependency Injection: принимает shutdown_event для координации
    - Single Purpose: отвечает только за обработку OAuth2 callback
    - Separation of Concerns: логика работы с файлами вынесена в CodeFileHandler
    
    OAuth2 Authorization Code Flow интеграция:
    1. OAuth2 провайдер перенаправляет пользователя на /callback
    2. Сервер выделяет код авторизации из query параметров
    3. Код сохраняется в временный файл через CodeFileHandler
    4. Пользователю отображается страница успешной авторизации
    5. Сервер получает сигнал о завершении через shutdown_event
    
    Пример использования:
        >>> import asyncio
        >>> shutdown_event = asyncio.Event()
        >>> app = create_app(shutdown_event)
        >>> # Приложение готово к запуску через uvicorn
        >>> # После callback сервер автоматически завершит работу
    
    Пример callback URL:
        http://127.0.0.1:8080/callback?code=AUTH_CODE_FROM_PROVIDER&state=random_state
    
    Args:
        shutdown_event: Событие asyncio для координации завершения сервера.
                       Событие будет установлено после успешного 
                       получения кода авторизации.
    
    Returns:
        FastAPI: Настроенное приложение FastAPI с обработчиком callback.
                 Приложение готово для запуска через uvicorn.
    
    Note:
        Приложение создает новый экземпляр CodeFileHandler при каждом вызове.
        Это обеспечивает чистоту состояния и изоляцию между запусками.
    """
    logger.debug("Создание FastAPI приложения для OAuth2 callback сервера")
    app = FastAPI(
        title="OAuth2 Callback Server",
        description="Локальный сервер для обработки OAuth2 Authorization Code callback",
        version="1.0.0"
    )
    code_handler = CodeFileHandler()

    @app.get("/callback")
    async def callback_handler(code: str = Query(None)):
        """Обрабатывает OAuth2 Authorization Code callback запросы.
        
        Этот endpoint является ключевым компонентом OAuth2 Authorization Code Flow.
        Он принимает код авторизации от OAuth2 провайдера, сохраняет его
        для последующего обмена на токены и инициирует завершение работы сервера.
        
        Порядок обработки:
        1. Проверяет наличие кода в query параметрах
        2. Сохраняет код в временный файл через CodeFileHandler
        3. Устанавливает shutdown_event для сигнализации о завершении
        4. Возвращает HTML страницу с сообщением о результате
        
        Архитектурные особенности:
        - Асинхронный обработчик для неблокирующей обработки
        - Логирование всех ключевых моментоВ (с маскировкой кода)
        - Обработка ошибок с соответствующими HTTP статусами
        - Пользовательские HTML ответы на русском языке
        
        Пример callback URL от Google OAuth2:
            GET /callback?code=4/0AX4XfWjYZ...&scope=profile+email&state=random_value
            
        Пример callback URL от GitHub OAuth2:
            GET /callback?code=github_auth_code_123...&state=csrf_token
        
        Args:
            code: Код авторизации, полученный от OAuth2 провайдера.
                  Может быть None, если произошла ошибка авторизации.
        
        Returns:
            HTMLResponse: HTML страница с сообщением о результате авторизации.
                         Статус 200 при успехе, 400 при ошибке.
        
        Side Effects:
            - Сохраняет код авторизации в временный файл
            - Устанавливает shutdown_event, что приводит к завершению сервера
            - Логирует операции (с маскировкой конфиденциальных данных)
        
        Note:
            URL для callback должен быть зарегистрирован в настройках OAuth2 приложения.
            Обычно это http://127.0.0.1:8080/callback или http://localhost:8080/callback.
        """
        logger.info("Получен callback запрос от OAuth2 провайдера")
        
        if code:
            logger.info("Получен код авторизации: %s...", code[:10])
            logger.debug("Сохранение кода авторизации в файл")
            code_handler.write(code)
            
            logger.info("Отправляется сигнал о завершении авторизации")
            shutdown_event.set()  # Сигнализируем о завершении
            
            return HTMLResponse("Авторизация успешно завершена. Вы можете закрыть это окно и вернуться в приложение.")
        
        logger.error("Код авторизации отсутствует в callback запросе")
        return HTMLResponse("Ошибка авторизации. Пожалуйста, попробуйте снова.", status_code=400)

    logger.debug("FastAPI приложение создано и готово к использованию")
    return app