# src/auth/router.py
# --- agent_meta ---
# role: auth-router
# owner: @backend
# contract: FastAPI роуты для регистрации, входа/выхода, профиля и организаций
# last_reviewed: 2025-08-21
# interfaces:
#   - POST /auth/signup
#   - POST /auth/login
#   - POST /auth/logout
#   - GET /me
#   - POST /orgs
# --- /agent_meta ---

import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.utils import get_logger
from .deps import require_session_id, COOKIE_NAME
from .exceptions import AuthenticationError, InvalidCredentialsError, UserExistsError
from .models import LoginRequest, MeOut, SignupRequest
from .service import AuthService
from .storage import AuthStorage


router = APIRouter()

# Логгер для роутера
logger = get_logger("auth.router")

_storage = AuthStorage()
_service = AuthService(_storage)

# Конфигурация cookie для безопасности
COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "lax").lower()
COOKIE_DOMAIN = os.getenv("AUTH_COOKIE_DOMAIN", None)


def _set_sid_cookie(response: Response, sid: str) -> None:
    """Установка secure cookie с сессионным идентификатором.
    
    Параметры безопасности:
    - HttpOnly: предотвращает доступ через JavaScript
    - Secure: передача только по HTTPS (конфигурируемо)
    - SameSite: защита от CSRF-атак
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=sid,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,  # "lax" | "strict" | "none"
        domain=COOKIE_DOMAIN,
        path="/",
    )


@router.post("/auth/signup")
def signup(data: SignupRequest, response: Response, request: Request):
    """Регистрация нового пользователя с автоматическим входом."""
    try:
        out = _service.signup(email=data.email, password=data.password, org_name=data.org_name)
    except UserExistsError as e:
        logger.warning(f"Signup attempt for existing user: {e.email}")
        raise HTTPException(status_code=409, detail={"error_code": e.error_code, "message": str(e)})
    except AuthenticationError as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=400, detail={"error_code": e.error_code, "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected signup error: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})
        
    # Авто-вход: создаём сессию для нового пользователя
    try:
        login_out = _service.login(email=data.email, password=data.password, request=request)
        _set_sid_cookie(response, login_out["session"]["id"])
    except Exception as e:
        logger.error(f"Auto-login after signup failed for {data.email}: {e}")
        # Не проваливаем всю регистрацию из-за ошибки авто-входа
        
    user = out["user"]
    return {"user": {"id": user["id"], "email": user["email"]}, "org_id": out["org"]["id"]}


@router.post("/auth/login")
def login(data: LoginRequest, response: Response, request: Request):
    """Аутентификация пользователя и создание сессии."""
    try:
        out = _service.login(email=data.email, password=data.password, request=request)
    except InvalidCredentialsError as e:
        # Не логируем детали ошибки на уровне router - это уже делает service
        raise HTTPException(status_code=401, detail={"error_code": e.error_code, "message": str(e)})
    except AuthenticationError as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail={"error_code": e.error_code, "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected login error: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})
        
    _set_sid_cookie(response, out["session"]["id"])
    return {"ok": True}


@router.post("/auth/logout")
def logout(response: Response, sid: str = Depends(require_session_id)):
    """Выход пользователя и удаление сессии."""
    try:
        _service.logout(sid)
        # Очищаем cookie после успешного удаления сессии
        response.delete_cookie(key=COOKIE_NAME, path="/", domain=COOKIE_DOMAIN)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Logout error for session {sid}: {e}")
        # Даже при ошибке очищаем cookie для безопасности
        response.delete_cookie(key=COOKIE_NAME, path="/", domain=COOKIE_DOMAIN)
        raise HTTPException(status_code=500, detail={"error_code": "LOGOUT_ERROR", "message": "Logout failed"})


@router.get("/me", response_model=MeOut)
def me(sid: str = Depends(require_session_id)):
    """Получение информации о текущем пользователе."""
    try:
        me_info = _service.get_me(sid)
        if not me_info:
            logger.debug(f"Unauthorized access attempt with session: {sid}")
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session invalid or expired"})
            
        user = me_info["user"]
        return {
            "user": {"id": user["id"], "email": user["email"]},
            "org_id": me_info["org_id"],
            "role": me_info["role"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user info for session {sid}: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})


@router.post("/orgs")
def create_org(name: str, sid: str = Depends(require_session_id)):
    """Создание новой организации текущим пользователем."""
    try:
        me_info = _service.get_me(sid)
        if not me_info:
            logger.warning(f"Unauthorized org creation attempt with session: {sid}")
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session invalid or expired"})
            
        org = _service.create_org(user_id=me_info["user"]["id"], name=name)
        return {"org_id": org["id"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization '{name}' for session {sid}: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "ORG_CREATION_ERROR", "message": "Failed to create organization"})

