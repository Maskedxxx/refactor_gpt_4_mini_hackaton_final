# src/auth/storage.py
# --- agent_meta ---
# role: auth-storage
# owner: @backend
# contract: SQLite-хранилище для пользователей, организаций, членств и сессий
# last_reviewed: 2025-08-21
# interfaces:
#   - AuthStorage.create_user(email, password_hash) -> dict
#   - AuthStorage.get_user_by_email(email) -> dict | None
#   - AuthStorage.get_user_by_id(user_id) -> dict | None
#   - AuthStorage.create_org(name) -> dict
#   - AuthStorage.create_membership(user_id, org_id, role, status)
#   - AuthStorage.get_memberships_for_user(user_id) -> list[dict]
#   - AuthStorage.create_session(user_id, org_id, expires_at, ua_hash, ip_hash) -> dict
#   - AuthStorage.get_session(session_id) -> dict | None
#   - AuthStorage.delete_session(session_id) -> None
# --- /agent_meta ---

import os
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional


class AuthStorage:
    """Слой доступа к данным для системы аутентификации.
    
    Отвечает за хранение и извлечение данных о пользователях, организациях,
    членствах и сессиях в SQLite базе данных.
    
    Использует простую реляционную модель для MVP.
    """
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or os.getenv("WEBAPP_DB_PATH", "app.sqlite3")
        
        # Отключаем check_same_thread=False для возможности использования в FastAPI,
        # где запросы могут выполняться в разных потоках.
        # Однако это ответственность приложения - обеспечить потокобезопасность.
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        
        # Настраиваем row_factory для удобного доступа к столбцам по именам
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        """Инициализация схемы базы данных для аутентификации.
        
        Создает таблицы, если они еще не существуют.
        Использует CREATE TABLE IF NOT EXISTS для безопасности.
        """
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS memberships (
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                PRIMARY KEY (user_id, org_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS auth_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                expires_at REAL NOT NULL,
                ua_hash TEXT,
                ip_hash TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
            """
        )
        self._conn.commit()

    # Users
    def create_user(self, email: str, password_hash: str) -> Dict[str, Any]:
        """Создание нового пользователя в базе данных.
        
        Args:
            email: Нормализованный email пользователя
            password_hash: Хеш пароля в формате scrypt
            
        Returns:
            Словарь с данными созданного пользователя
        """
        user_id = str(uuid.uuid4())
        now = time.time()
        self._conn.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, email.lower(), password_hash, now),
        )
        self._conn.commit()
        return {"id": user_id, "email": email.lower(), "created_at": now}

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Поиск пользователя по email.
        
        Args:
            email: Адрес электронной почты (нормализуется в lowercase)
            
        Returns:
            Словарь с данными пользователя или None, если не найден
        """
        cur = self._conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
            (email.lower(),),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    # Orgs
    def create_org(self, name: str) -> Dict[str, Any]:
        org_id = str(uuid.uuid4())
        now = time.time()
        self._conn.execute(
            "INSERT INTO organizations (id, name, created_at) VALUES (?, ?, ?)",
            (org_id, name, now),
        )
        self._conn.commit()
        return {"id": org_id, "name": name, "created_at": now}

    # Memberships
    def create_membership(self, user_id: str, org_id: str, role: str, status: str = "active") -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO memberships (user_id, org_id, role, status) VALUES (?, ?, ?, ?)",
            (user_id, org_id, role, status),
        )
        self._conn.commit()

    def get_memberships_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT user_id, org_id, role, status FROM memberships WHERE user_id = ?",
            (user_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    # Sessions
    def create_session(
        self,
        user_id: str,
        org_id: str,
        expires_at: float,
        ua_hash: Optional[str],
        ip_hash: Optional[str],
    ) -> Dict[str, Any]:
        """Создание новой пользовательской сессии.
        
        Args:
            user_id: Идентификатор пользователя
            org_id: Идентификатор организации
            expires_at: Unix timestamp времени истечения
            ua_hash: Хеш User-Agent для дополнительной безопасности
            ip_hash: Хеш IP-адреса для дополнительной безопасности
            
        Returns:
            Словарь с данными созданной сессии
        """
        sid = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO auth_sessions (id, user_id, org_id, expires_at, ua_hash, ip_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (sid, user_id, org_id, expires_at, ua_hash, ip_hash),
        )
        self._conn.commit()
        return {"id": sid, "user_id": user_id, "org_id": org_id, "expires_at": expires_at}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT id, user_id, org_id, expires_at, ua_hash, ip_hash FROM auth_sessions WHERE id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: str) -> None:
        self._conn.execute("DELETE FROM auth_sessions WHERE id = ?", (session_id,))
        self._conn.commit()
