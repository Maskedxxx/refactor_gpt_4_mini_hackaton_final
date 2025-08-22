# src/auth/deps.py
# --- agent_meta ---
# role: auth-dependencies
# owner: @backend
# contract: FastAPI зависимости для извлечения текущего пользователя/сессии
# last_reviewed: 2025-08-21
# interfaces:
#   - get_current_session_id(request) -> str | None
#   - require_session_id(request) -> str (HTTP 401 on missing)
# --- /agent_meta ---

from fastapi import Cookie, HTTPException, Request
from typing import Optional


COOKIE_NAME = "sid"


def get_current_session_id(sid: Optional[str] = Cookie(default=None, alias=COOKIE_NAME)) -> Optional[str]:
    return sid


def require_session_id(sid: Optional[str] = Cookie(default=None, alias=COOKIE_NAME)) -> str:
    if not sid:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return sid

