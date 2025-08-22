# src/auth/service.py
# --- agent_meta ---
# role: auth-service
# owner: @backend
# contract: Бизнес-логика регистрации, входа, сессий и орг
# last_reviewed: 2025-08-21
# interfaces:
#   - signup(email, password, org_name?) -> dict
#   - login(email, password, request) -> dict
#   - logout(session_id) -> None
#   - get_me(session_id) -> dict | None
#   - create_org(user_id, name) -> dict
# --- /agent_meta ---

import hashlib
import os
import time
from typing import Dict, Optional

from fastapi import Request

from src.utils import get_logger
from .crypto import hash_password, verify_password
from .exceptions import InvalidCredentialsError, UserExistsError
from .storage import AuthStorage


SESSION_TTL_SEC = int(os.getenv("AUTH_SESSION_TTL_SEC", "604800"))  # 7 дней

# Настройка логгера для аудита безопасности
logger = get_logger("auth.service")


def _hash_str(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class AuthService:
    """Сервис аутентификации и управления пользователями.
    
    Предоставляет бизнес-логику для регистрации, входа/выхода пользователей,
    управления сессиями и организациями.
    """
    
    def __init__(self, storage: AuthStorage) -> None:
        self.storage = storage

    # Users / auth
    def signup(self, email: str, password: str, org_name: Optional[str] = None) -> Dict:
        """Регистрация нового пользователя с автоматическим созданием организации.
        
        Args:
            email: Адрес электронной почты пользователя
            password: Пароль в открытом виде
            org_name: Имя организации (опционально)
            
        Returns:
            Словарь с данными пользователя и организации
            
        Raises:
            UserExistsError: Если пользователь с таким email уже существует
        """
        logger.info(f"Signup attempt for email: {email}")
        
        existing = self.storage.get_user_by_email(email)
        if existing:
            logger.warning(f"Signup failed - user already exists: {email}")
            raise UserExistsError(email)
            
        pwd_hash = hash_password(password)
        user = self.storage.create_user(email=email, password_hash=pwd_hash)
        org = self.storage.create_org(org_name or f"Org of {email}")
        self.storage.create_membership(user_id=user["id"], org_id=org["id"], role="org_admin")
        
        logger.info(f"User successfully registered: {email}, user_id: {user['id']}, org_id: {org['id']}")
        return {"user": user, "org": org}

    def login(self, email: str, password: str, request: Request) -> Dict:
        """Аутентификация пользователя и создание новой сессии.
        
        Args:
            email: Адрес электронной почты
            password: Пароль в открытом виде
            request: FastAPI Request для извлечения метаданных
            
        Returns:
            Словарь с данными сессии, пользователя и организации
            
        Raises:
            InvalidCredentialsError: При неверных учетных данных
        """
        ua = request.headers.get("user-agent", "")
        ip = request.client.host if request.client else "unknown"
        
        logger.info(f"Login attempt for email: {email}, ip: {ip}")
        
        user = self.storage.get_user_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            logger.warning(f"Login failed - invalid credentials for email: {email}, ip: {ip}")
            raise InvalidCredentialsError(email)
            
        # Выбираем первую активную membership как текущую организацию.
        # Это упрощенная логика для MVP - в будущем можно добавить выбор организации при логине.
        memberships = self.storage.get_memberships_for_user(user["id"]) or []
        if not memberships:
            # Fallback: создать дефолтную организацию, если у пользователя нет членства
            # (это может произойти при миграции данных или удалении организаций)
            logger.info(f"Creating fallback organization for user: {user['email']}")
            org = self.storage.create_org(f"Org of {user['email']}")
            self.storage.create_membership(user_id=user["id"], org_id=org["id"], role="org_admin")
            org_id = org["id"]
        else:
            org_id = memberships[0]["org_id"]

        now = time.time()
        session = self.storage.create_session(
            user_id=user["id"],
            org_id=org_id,
            expires_at=now + SESSION_TTL_SEC,
            ua_hash=_hash_str(ua),
            ip_hash=_hash_str(ip),
        )
        
        logger.info(f"User successfully logged in: {email}, user_id: {user['id']}, session_id: {session['id']}, ip: {ip}")
        return {"session": session, "user": user, "org_id": org_id}

    def logout(self, session_id: str) -> None:
        """Завершение пользовательской сессии.
        
        Args:
            session_id: Идентификатор сессии для удаления
        """
        # Получаем информацию о сессии перед удалением для логирования
        session = self.storage.get_session(session_id)
        if session:
            logger.info(f"User logged out: user_id: {session['user_id']}, session_id: {session_id}")
        
        self.storage.delete_session(session_id)

    # Me
    def get_me(self, session_id: str) -> Optional[Dict]:
        """Получение информации о текущем пользователе по сессии.
        
        Args:
            session_id: Идентификатор активной сессии
            
        Returns:
            Словарь с данными пользователя, организации и роли или None
        """
        sess = self.storage.get_session(session_id)
        if not sess:
            logger.debug(f"Session not found: {session_id}")
            return None
            
        if sess["expires_at"] < time.time():
            logger.info(f"Session expired and removed: {session_id}, user_id: {sess['user_id']}")
            self.storage.delete_session(session_id)
            return None
            
        user = self.storage.get_user_by_id(sess["user_id"]) or {}
        
        # Определяем роль пользователя в текущей организации из таблицы memberships
        memberships = self.storage.get_memberships_for_user(sess["user_id"]) or []
        role = "viewer"  # роль по умолчанию
        for m in memberships:
            if m["org_id"] == sess["org_id"]:
                role = m["role"]
                break
                
        return {"user": user, "org_id": sess["org_id"], "role": role}

    # Orgs
    def create_org(self, user_id: str, name: str) -> Dict:
        """Создание новой организации с назначением создателя администратором.
        
        Args:
            user_id: Идентификатор пользователя-создателя
            name: Название организации
            
        Returns:
            Словарь с данными созданной организации
        """
        org = self.storage.create_org(name)
        self.storage.create_membership(user_id=user_id, org_id=org["id"], role="org_admin")
        
        logger.info(f"Organization created: {name}, org_id: {org['id']}, created_by: {user_id}")
        return org

