# src/auth/router.py
# --- agent_meta ---
# role: auth-router
# owner: @backend
# contract: FastAPI роуты для регистрации, входа/выхода, профиля, организаций и HH интеграции
# last_reviewed: 2025-08-23
# interfaces:
#   - POST /auth/signup
#   - POST /auth/login
#   - POST /auth/logout
#   - GET /me
#   - POST /orgs
#   - GET /auth/hh/status
#   - GET /auth/hh/connect
#   - GET /auth/hh/callback
#   - POST /auth/hh/disconnect
# --- /agent_meta ---

import os
import time
import hashlib
import aiohttp
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.utils import get_logger
from src.hh_adapter.config import HHSettings
from .oauth_utils import exchange_code_for_tokens
from .deps import require_session_id, COOKIE_NAME
from .exceptions import AuthenticationError, InvalidCredentialsError, UserExistsError
from .models import LoginRequest, MeOut, SignupRequest
from .service import AuthService
from .storage import AuthStorage
from .hh_service import HHAccountService


router = APIRouter()

# Логгер для роутера
logger = get_logger("auth.router")

# Lazy initialization для тестирования
_storage = None
_service = None
_hh_service = None
_hh_settings = None


def _get_storage() -> AuthStorage:
    """Lazy initialization AuthStorage."""
    global _storage
    if _storage is None:
        _storage = AuthStorage()
    return _storage


def _get_service() -> AuthService:
    """Lazy initialization AuthService."""
    global _service
    if _service is None:
        _service = AuthService(_get_storage())
    return _service


def _get_hh_service() -> HHAccountService:
    """Lazy initialization HHAccountService."""
    global _hh_service
    if _hh_service is None:
        _hh_service = HHAccountService(_get_storage())
    return _hh_service


def _get_hh_settings() -> HHSettings:
    """Lazy initialization HHSettings."""
    global _hh_settings
    if _hh_settings is None:
        _hh_settings = HHSettings()
    return _hh_settings

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
        out = _get_service().signup(email=data.email, password=data.password, org_name=data.org_name)
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
        login_out = _get_service().login(email=data.email, password=data.password, request=request)
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
        out = _get_service().login(email=data.email, password=data.password, request=request)
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
        _get_service().logout(sid)
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
        me_info = _get_service().get_me(sid)
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
        me_info = _get_service().get_me(sid)
        if not me_info:
            logger.warning(f"Unauthorized org creation attempt with session: {sid}")
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session invalid or expired"})
            
        org = _get_service().create_org(user_id=me_info["user"]["id"], name=name)
        return {"org_id": org["id"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating organization '{name}' for session {sid}: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "ORG_CREATION_ERROR", "message": "Failed to create organization"})


# =============================================================================
# HH.ru OAuth2 интеграция
# =============================================================================

def _hash_str(s: Optional[str]) -> Optional[str]:
    """Хеширует строку для безопасного хранения."""
    if not s:
        return None
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@router.get("/auth/hh/status")
def hh_status(sid: str = Depends(require_session_id)):
    """Проверяет статус подключения HH аккаунта текущего пользователя."""
    try:
        me_info = _get_service().get_me(sid)
        if not me_info:
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session invalid"})
        
        user_id = me_info["user"]["id"] 
        org_id = me_info["org_id"]
        
        is_connected = _get_hh_service().is_hh_connected(user_id, org_id)
        hh_account = _get_hh_service().get_hh_account(user_id, org_id) if is_connected else None
        
        result = {
            "is_connected": is_connected,
            "expires_in_seconds": hh_account.expires_in_seconds if hh_account else None,
            "connected_at": hh_account.connected_at if hh_account else None,
        }
        
        logger.info(f"HH status для пользователя {user_id}: connected={is_connected}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка проверки HH статуса для сессии {sid}: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "HH_STATUS_ERROR", "message": "Failed to check HH status"})


@router.get("/auth/hh/connect")
def hh_connect_start(request: Request, sid: str = Depends(require_session_id)):
    """Инициирует подключение HH аккаунта к текущему пользователю."""
    try:
        me_info = _get_service().get_me(sid)
        if not me_info:
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session invalid"})
        
        user_id = me_info["user"]["id"]
        org_id = me_info["org_id"]
        
        # Проверяем не подключен ли уже HH
        if _get_hh_service().is_hh_connected(user_id, org_id):
            logger.info(f"HH уже подключен для пользователя {user_id}")
            raise HTTPException(status_code=409, detail={"error_code": "HH_ALREADY_CONNECTED", "message": "HH account already connected"})
        
        # Создаем state для OAuth2 с привязкой к пользователю  
        state = secrets.token_urlsafe(32)
        
        # Сохраняем state в БД с TTL
        ua_hash = _hash_str(request.headers.get("User-Agent"))
        ip_hash = _hash_str(str(request.client.host) if request.client else None)
        
        _get_storage().save_oauth_state(
            state=state,
            user_id=user_id,
            org_id=org_id,
            session_id=sid,
            ua_hash=ua_hash,
            ip_hash=ip_hash,
            ttl_seconds=600  # 10 минут
        )
        
        # Формируем OAuth2 URL
        auth_url = (
            f"https://hh.ru/oauth/authorize?"
            f"response_type=code&"
            f"client_id={_get_hh_settings().client_id}&" 
            f"redirect_uri={_get_hh_settings().redirect_uri}&"
            f"state={state}"
        )
        
        logger.info(f"Начинаем подключение HH для пользователя {user_id}")
        return {"auth_url": auth_url, "state": state}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка инициации подключения HH для сессии {sid}: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "HH_CONNECT_ERROR", "message": "Failed to initiate HH connection"})


@router.get("/auth/hh/callback")  
async def hh_callback(code: str, state: str, request: Request):
    """Обрабатывает callback от HH.ru и привязывает аккаунт к пользователю."""
    try:
        # Проверяем state в БД (автоматически проверяет TTL)
        state_data = _get_storage().get_oauth_state(state)
        if not state_data:
            logger.warning(f"Недействительный или устаревший state: {state}")
            raise HTTPException(status_code=400, detail={"error_code": "INVALID_STATE", "message": "Invalid or expired state"})
        
        # Удаляем использованный state (consume)
        _get_storage().delete_oauth_state(state)
        
        user_id = state_data["user_id"]
        org_id = state_data["org_id"]
        
        # Обмениваем код на токены
        async with aiohttp.ClientSession() as session:
            try:
                tokens = await exchange_code_for_tokens(session, _get_hh_settings(), code)
                logger.info(f"Токены HH получены для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка обмена кода на токены для пользователя {user_id}: {e}")
                raise HTTPException(status_code=400, detail={"error_code": "TOKEN_EXCHANGE_FAILED", "message": f"Token exchange failed: {e}"})
        
        # Сохраняем HH аккаунт
        ua_hash = _hash_str(request.headers.get("User-Agent"))
        ip_hash = _hash_str(str(request.client.host) if request.client else None)
        
        _get_hh_service().connect_hh_account(
            user_id=user_id,
            org_id=org_id,
            tokens=tokens,
            ua_hash=ua_hash,
            ip_hash=ip_hash
        )
        
        return {"message": "HH account connected successfully", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка HH callback: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "HH_CALLBACK_ERROR", "message": "HH callback processing failed"})


@router.post("/auth/hh/disconnect")
def hh_disconnect(sid: str = Depends(require_session_id)):
    """Отключает HH аккаунт от текущего пользователя."""
    try:
        me_info = _get_service().get_me(sid)
        if not me_info:
            raise HTTPException(status_code=401, detail={"error_code": "UNAUTHORIZED", "message": "Session invalid"})
        
        user_id = me_info["user"]["id"]
        org_id = me_info["org_id"] 
        
        success = _get_hh_service().disconnect_hh_account(user_id, org_id)
        
        if success:
            logger.info(f"HH аккаунт отключен для пользователя {user_id}")
            return {"message": "HH account disconnected successfully"}
        else:
            raise HTTPException(status_code=404, detail={"error_code": "HH_NOT_CONNECTED", "message": "HH account was not connected"})
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка отключения HH для сессии {sid}: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "HH_DISCONNECT_ERROR", "message": "Failed to disconnect HH account"})

