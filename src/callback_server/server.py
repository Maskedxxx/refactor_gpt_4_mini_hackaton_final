# src/callback_server/server.py
# --- agent_meta ---
# role: callback-server-logic
# owner: @backend
# contract: Handles the OAuth callback, saves the code, and signals shutdown.
# last_reviewed: 2025-07-24
# interfaces:
#   - create_app()
# --- /agent_meta ---

import asyncio
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from src.callback_server.code_handler import CodeFileHandler
from src.utils import get_logger

logger = get_logger(__name__)

def create_app(shutdown_event: asyncio.Event) -> FastAPI:
    """Создает экземпляр FastAPI приложения с обработчиком callback."""
    logger.debug("Создание FastAPI приложения для callback сервера")
    app = FastAPI(title="Callback Local Server")
    code_handler = CodeFileHandler()

    @app.get("/callback")
    async def callback_handler(code: str = Query(None)):
        """Обработчик callback запроса от OAuth2."""
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