# src/webapp/storage_docs.py
# --- agent_meta ---
# role: webapp-document-storage
# owner: @backend
# contract: Персистентное хранение ResumeInfo/VacancyInfo и сессий с новой архитектурой user_id + org_id
# last_reviewed: 2025-08-24
# interfaces:
#   - ResumeStore.save(user_id: str, org_id: str, model: ResumeInfo, source_hash: str | None) -> str
#   - ResumeStore.get(resume_id: str) -> ResumeInfo | None
#   - ResumeStore.find_by_hash(user_id: str, org_id: str, source_hash: str) -> tuple[str, ResumeInfo] | None
#   - VacancyStore.save(user_id: str, org_id: str, model: VacancyInfo, source_url: str, source_hash: str | None) -> str
#   - VacancyStore.get(vacancy_id: str) -> VacancyInfo | None
#   - VacancyStore.find_by_url_or_hash(user_id: str, org_id: str, url: str, source_hash: str | None) -> tuple[str, VacancyInfo] | None
#   - SessionStore.create(user_id: str, org_id: str, resume_id: str, vacancy_id: str, ttl_sec: int | None = None) -> str
#   - SessionStore.get(session_id: str) -> dict | None
#   - SessionStore.delete(session_id: str) -> None
# --- /agent_meta ---

from __future__ import annotations

import os
import sqlite3
import time
import uuid
from typing import Optional, Tuple, Dict, Any

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo


def _db_path() -> str:
    return os.getenv("WEBAPP_DB_PATH", "app.sqlite3")


class ResumeStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _db_path()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        # Таблица уже создана в новом формате миграцией, но проверяем на всякий случай
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_docs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                source_hash TEXT,
                title TEXT,
                data_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_resume_user_org ON resume_docs(user_id, org_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_resume_hash ON resume_docs(source_hash)")
        self._conn.commit()

    def save(self, user_id: str, org_id: str, model: ResumeInfo, source_hash: Optional[str] = None) -> str:
        rid = str(uuid.uuid4())
        payload = model.model_dump_json()
        title = model.title if hasattr(model, "title") else None
        self._conn.execute(
            "INSERT INTO resume_docs (id, user_id, org_id, source_hash, title, data_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rid, user_id, org_id, source_hash, title, payload, float(time.time())),
        )
        self._conn.commit()
        return rid

    def get(self, resume_id: str) -> Optional[ResumeInfo]:
        cur = self._conn.execute(
            "SELECT data_json FROM resume_docs WHERE id = ?",
            (resume_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return ResumeInfo.model_validate_json(row[0])

    def find_by_hash(self, user_id: str, org_id: str, source_hash: str) -> Optional[Tuple[str, ResumeInfo]]:
        cur = self._conn.execute(
            """
            SELECT id, data_json 
            FROM resume_docs 
            WHERE user_id = ? AND org_id = ? AND source_hash = ? 
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id, org_id, source_hash),
        )
        row = cur.fetchone()
        if not row:
            return None
        return row[0], ResumeInfo.model_validate_json(row[1])


class VacancyStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _db_path()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        # Таблица уже создана в новом формате миграцией, но проверяем на всякий случай
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vacancy_docs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_hash TEXT,
                name TEXT,
                data_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_vac_user_org ON vacancy_docs(user_id, org_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_vac_url ON vacancy_docs(source_url)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_vac_hash ON vacancy_docs(source_hash)")
        self._conn.commit()

    def save(
        self,
        user_id: str,
        org_id: str,
        model: VacancyInfo,
        source_url: str,
        source_hash: Optional[str] = None,
    ) -> str:
        vid = str(uuid.uuid4())
        payload = model.model_dump_json()
        name = model.name if hasattr(model, "name") else None
        self._conn.execute(
            "INSERT INTO vacancy_docs (id, user_id, org_id, source_url, source_hash, name, data_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (vid, user_id, org_id, source_url, source_hash, name, payload, float(time.time())),
        )
        self._conn.commit()
        return vid

    def get(self, vacancy_id: str) -> Optional[VacancyInfo]:
        cur = self._conn.execute(
            "SELECT data_json FROM vacancy_docs WHERE id = ?",
            (vacancy_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return VacancyInfo.model_validate_json(row[0])

    def find_by_url_or_hash(
        self, user_id: str, org_id: str, url: str, source_hash: Optional[str] = None
    ) -> Optional[Tuple[str, VacancyInfo]]:
        if source_hash:
            cur = self._conn.execute(
                """
                SELECT id, data_json FROM vacancy_docs 
                WHERE user_id = ? AND org_id = ? AND (source_url = ? OR source_hash = ?) 
                ORDER BY created_at DESC LIMIT 1
                """,
                (user_id, org_id, url, source_hash),
            )
        else:
            cur = self._conn.execute(
                """
                SELECT id, data_json FROM vacancy_docs 
                WHERE user_id = ? AND org_id = ? AND source_url = ? 
                ORDER BY created_at DESC LIMIT 1
                """,
                (user_id, org_id, url),
            )
        row = cur.fetchone()
        if not row:
            return None
        return row[0], VacancyInfo.model_validate_json(row[1])


class SessionStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self._db_path = db_path or _db_path()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        # Таблица уже создана в новом формате миграцией, но проверяем на всякий случай
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                org_id TEXT NOT NULL,
                resume_id TEXT NOT NULL,
                vacancy_id TEXT NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE,
                FOREIGN KEY(resume_id) REFERENCES resume_docs(id) ON DELETE CASCADE,
                FOREIGN KEY(vacancy_id) REFERENCES vacancy_docs(id) ON DELETE CASCADE
            )
            """
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_org ON sessions(user_id, org_id)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_exp ON sessions(expires_at)")
        self._conn.commit()

    def create(
        self, user_id: str, org_id: str, resume_id: str, vacancy_id: str, ttl_sec: Optional[int] = None
    ) -> str:
        sid = str(uuid.uuid4())
        now = float(time.time())
        exp = float(now + ttl_sec) if ttl_sec is not None else None
        self._conn.execute(
            "INSERT INTO sessions (id, user_id, org_id, resume_id, vacancy_id, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sid, user_id, org_id, resume_id, vacancy_id, now, exp),
        )
        self._conn.commit()
        return sid

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.execute(
            "SELECT user_id, org_id, resume_id, vacancy_id, created_at, expires_at FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        user_id, org_id, resume_id, vacancy_id, created_at, expires_at = row
        if expires_at is not None and float(expires_at) <= time.time():
            # протухла — удаляем
            self.delete(session_id)
            return None
        return {
            "user_id": user_id,
            "org_id": org_id,
            "resume_id": resume_id,
            "vacancy_id": vacancy_id,
            "created_at": float(created_at),
            "expires_at": float(expires_at) if expires_at is not None else None,
        }

    def delete(self, session_id: str) -> None:
        self._conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self._conn.commit()

