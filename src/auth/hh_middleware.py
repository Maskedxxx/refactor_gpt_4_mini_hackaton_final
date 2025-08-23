# src/auth/hh_middleware.py
# --- agent_meta ---
# role: hh-auth-middleware
# owner: @backend
# contract: Middleware для проверки HH авторизации перед доступом к LLM фичам
# last_reviewed: 2025-08-23
# interfaces:
#   - require_hh_connection(session_id: str) -> UserWithHH
#   - get_current_user_with_hh(session_id: str) -> UserWithHH | None
# --- /agent_meta ---

from typing import Optional, Dict, Any
from dataclasses import dataclass
from fastapi import HTTPException, Depends

from src.utils import get_logger
from .deps import require_session_id
from .service import AuthService
from .storage import AuthStorage
from .hh_service import HHAccountService, HHAccountInfo

logger = get_logger("auth.hh_middleware")

# DI-синглтоны для middleware
_storage = AuthStorage()
_auth_service = AuthService(_storage)
_hh_service = HHAccountService(_storage)


@dataclass
class UserWithHH:
    """Контекст пользователя с подтвержденным подключением HH."""
    user_id: str
    org_id: str
    user_email: str
    user_role: str
    hh_account: HHAccountInfo
    session_id: str


async def get_current_user_with_hh(
    session_id: str = Depends(require_session_id)
) -> Optional[UserWithHH]:
    """
    Получает текущего пользователя с HH подключением (без исключения).
    
    Args:
        session_id: Идентификатор сессии пользователя
        
    Returns:
        UserWithHH если пользователь аутентифицирован и HH подключен, иначе None
    """
    try:
        # Проверяем внутреннюю аутентификацию
        me_info = _auth_service.get_me(session_id)
        if not me_info:
            logger.debug(f"Невалидная сессия: {session_id}")
            return None
        
        user_id = me_info["user"]["id"]
        org_id = me_info["org_id"]
        
        # Проверяем HH подключение
        hh_account = _hh_service.get_hh_account(user_id, org_id)
        if not hh_account:
            logger.debug(f"HH не подключен для пользователя {user_id}")
            return None
        
        # Проверяем не истекли ли токены
        if hh_account.is_expired:
            logger.warning(f"HH токены истекли для пользователя {user_id}")
            return None
        
        return UserWithHH(
            user_id=user_id,
            org_id=org_id,
            user_email=me_info["user"]["email"],
            user_role=me_info["role"],
            hh_account=hh_account,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка проверки пользователя с HH для сессии {session_id}: {e}")
        return None


async def require_hh_connection(
    session_id: str = Depends(require_session_id)
) -> UserWithHH:
    """
    Требует подключения HH аккаунта для доступа к ресурсу.
    
    Middleware для защиты LLM фич. Проверяет:
    1. Валидность внутренней сессии пользователя
    2. Наличие подключенного HH аккаунта  
    3. Действительность HH токенов
    
    Args:
        session_id: Идентификатор сессии пользователя
        
    Returns:
        UserWithHH с полным контекстом пользователя
        
    Raises:
        HTTPException 401: если пользователь не аутентифицирован
        HTTPException 403: если HH аккаунт не подключен или токены истекли
    """
    try:
        # Проверяем внутреннюю аутентификацию
        me_info = _auth_service.get_me(session_id)
        if not me_info:
            logger.info(f"Отклонен доступ: невалидная сессия {session_id}")
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "UNAUTHORIZED", 
                    "message": "Session invalid or expired",
                    "action_required": "login"
                }
            )
        
        user_id = me_info["user"]["id"]
        org_id = me_info["org_id"]
        
        # Проверяем HH подключение
        hh_account = _hh_service.get_hh_account(user_id, org_id)
        if not hh_account:
            logger.info(f"Отклонен доступ к LLM фичам: HH не подключен для пользователя {user_id}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "HH_CONNECTION_REQUIRED",
                    "message": "HH.ru connection required to access LLM features", 
                    "action_required": "connect_hh"
                }
            )
        
        # Проверяем не истекли ли токены
        if hh_account.is_expired:
            logger.warning(f"Отклонен доступ: HH токены истекли для пользователя {user_id}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "HH_TOKEN_EXPIRED",
                    "message": "HH.ru tokens expired, please reconnect",
                    "action_required": "reconnect_hh"
                }
            )
        
        logger.info(f"Доступ к LLM фичам разрешен для пользователя {user_id}")
        
        return UserWithHH(
            user_id=user_id,
            org_id=org_id,
            user_email=me_info["user"]["email"],
            user_role=me_info["role"],
            hh_account=hh_account,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Критическая ошибка HH middleware для сессии {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "MIDDLEWARE_ERROR",
                "message": "Authentication middleware failed"
            }
        )


def get_user_context(user_with_hh: UserWithHH) -> Dict[str, Any]:
    """
    Извлекает контекст пользователя для использования в LLM pipeline.
    
    Args:
        user_with_hh: Пользователь с подтвержденным HH подключением
        
    Returns:
        Словарь с контекстом пользователя для sessions и LLM фич
    """
    return {
        "user_id": user_with_hh.user_id,
        "org_id": user_with_hh.org_id,
        "user_email": user_with_hh.user_email,
        "user_role": user_with_hh.user_role,
        "hh_expires_in": user_with_hh.hh_account.expires_in_seconds,
        "session_id": user_with_hh.session_id
    }