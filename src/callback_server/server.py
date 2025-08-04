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
    app = FastAPI(title="Callback Local Server")
    code_handler = CodeFileHandler()

    @app.get("/callback")
    async def callback_handler(code: str = Query(None)):
        """Обработчик callback запроса от OAuth2."""
        if code:
            logger.info(f"Получен код авторизации: {code[:10]}...")
            code_handler.write(code)
            shutdown_event.set()  # Сигнализируем о завершении
            return HTMLResponse("Авторизация успешно завершена. Вы можете закрыть это окно и вернуться в приложение.")
        
        logger.error("Код авторизации отсутствует в запросе")
        return HTMLResponse("Ошибка авторизации. Пожалуйста, попробуйте снова.", status_code=400)

    return app