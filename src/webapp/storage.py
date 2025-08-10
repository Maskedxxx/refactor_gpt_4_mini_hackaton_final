# --- agent_meta ---
# role: token-storage
# owner: @backend
# contract: Персистентное хранение OAuth2 токенов и oauth-state в SQLite
# last_reviewed: 2025-08-10
# interfaces:
#   - TokenStorage.get(hr_id: str) -> dict | None
#   - TokenStorage.save(hr_id: str, tokens: dict) -> None
#   - TokenStorage.delete(hr_id: str) -> None
#   - OAuthStateStore.create(hr_id: str, redirect_to: str) -> str
#   - OAuthStateStore.consume(state: str, ttl_sec: int = 600) -> dict | None
# --- /agent_meta ---

import os
import sqlite3
import time
import secrets
from typing import Optional, Dict, Any


class TokenStorage:
    """
    Хранилище токенов (пер-HR).
    Простейшая реализация на SQLite, рассчитанная на 1 контейнер = 1 школа.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or os.getenv("WEBAPP_DB_PATH", "app.sqlite3")
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tokens (
                hr_id TEXT PRIMARY KEY,
                access_token TEXT NOT NULL,
                refresh_token TEXT NOT NULL,
                expires_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, hr_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT access_token, refresh_token, expires_at FROM tokens WHERE hr_id = ?",
            (hr_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "access_token": row[0],
            "refresh_token": row[1],
            "expires_at": float(row[2]),
        }

    def save(self, hr_id: str, tokens: Dict[str, Any]) -> None:
        self._conn.execute(
            "REPLACE INTO tokens (hr_id, access_token, refresh_token, expires_at) VALUES (?, ?, ?, ?)",
            (
                hr_id,
                tokens["access_token"],
                tokens["refresh_token"],
                float(tokens["expires_at"]),
            ),
        )
        self._conn.commit()

    def delete(self, hr_id: str) -> None:
        self._conn.execute("DELETE FROM tokens WHERE hr_id = ?", (hr_id,))
        self._conn.commit()


class OAuthStateStore:
    """
    Простое состояние OAuth2 для защиты от CSRF и связывания запроса.
    Сохраняет state -> {hr_id, redirect_to, created_at}.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or os.getenv("WEBAPP_DB_PATH", "app.sqlite3")
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_state (
                state TEXT PRIMARY KEY,
                hr_id TEXT NOT NULL,
                redirect_to TEXT,
                created_at REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def create(self, hr_id: str, redirect_to: Optional[str] = None) -> str:
        state = secrets.token_urlsafe(32)
        now = time.time()
        self._conn.execute(
            "INSERT INTO oauth_state (state, hr_id, redirect_to, created_at) VALUES (?, ?, ?, ?)",
            (state, hr_id, redirect_to or "", now),
        )
        self._conn.commit()
        return state

    def consume(self, state: str, ttl_sec: int = 600) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT hr_id, redirect_to, created_at FROM oauth_state WHERE state = ?",
            (state,),
        )
        row = cur.fetchone()
        if not row:
            return None
        hr_id, redirect_to, created_at = row[0], row[1], float(row[2])
        # TTL проверка
        if time.time() - created_at > ttl_sec:
            # протухло
            self._conn.execute("DELETE FROM oauth_state WHERE state = ?", (state,))
            self._conn.commit()
            return None

        # consume (удаляем запись)
        self._conn.execute("DELETE FROM oauth_state WHERE state = ?", (state,))
        self._conn.commit()
        return {"hr_id": hr_id, "redirect_to": redirect_to or None}
