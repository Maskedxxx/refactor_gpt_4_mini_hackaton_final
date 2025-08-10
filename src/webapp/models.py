# src/webapp/models.py
# --- agent_meta ---
# role: webapp-models
# owner: @backend
# contract: Pydantic модели данных для webapp (TokenRecord)
# last_reviewed: 2025-08-10
# interfaces:
#   - TokenRecord(access_token: str, refresh_token: str, expires_at: float)
#   - TokenRecord.expires_in(now: float | None = None) -> int
#   - TokenRecord.is_expired(now: float | None = None, skew: int = 0) -> bool
# --- /agent_meta ---

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class TokenRecord(BaseModel):
    """
    Модель пары токенов HH.ru и времени их истечения (Unix timestamp).

    Назначение:
    - Упростить работу с токенами (строгая схема и вспомогательные методы)
    - Минимизировать словарную адресацию по строковым ключам в коде
    - Сохранить совместимость со стореджем (конвертация в/из dict)
    """

    access_token: str = Field(..., description="Токен доступа (Bearer)")
    refresh_token: str = Field(..., description="Токен обновления access_token")
    expires_at: float = Field(..., description="Момент истечения access_token (Unix time)")

    def expires_in(self, now: Optional[float] = None) -> int:
        now_ts = float(now) if now is not None else time.time()
        return max(0, int(self.expires_at - now_ts))

    def is_expired(self, now: Optional[float] = None, skew: int = 0) -> bool:
        """
        Проверяет истечение токена с учётом сдвига (skew), чтобы обновлять заранее.
        skew в секундах, по умолчанию 0.
        """
        now_ts = float(now) if now is not None else time.time()
        return (self.expires_at - skew) <= now_ts

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "TokenRecord":
        return cls(
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            expires_at=float(row["expires_at"]),
        )

    def to_row(self) -> Dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": float(self.expires_at),
        }
