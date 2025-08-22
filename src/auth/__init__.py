# src/auth/__init__.py
# --- agent_meta ---
# role: auth-module
# owner: @backend
# contract: Пакет аутентификации/авторизации (роуты /auth/*, /orgs)
# last_reviewed: 2025-08-21
# interfaces:
#   - router: FastAPI APIRouter с эндпоинтами авторизации
# --- /agent_meta ---

from .router import router  # re-export

__all__ = ["router"]

