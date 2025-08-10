# --- agent_meta ---
# role: webapp-services
# owner: @backend
# contract: Обвязка над HHTokenManager c персистентностью и локом обновления
# last_reviewed: 2025-08-10
# interfaces:
#   - PersistentTokenManager.get_valid_access_token() -> str
#   - exchange_code_for_tokens(session, settings, code) -> dict
# --- /agent_meta ---

import asyncio
import time
from typing import Dict, Any

import aiohttp

from src.hh_adapter.config import HHSettings
from src.hh_adapter.tokens import HHTokenManager
from src.webapp.storage import TokenStorage


class PersistentTokenManager(HHTokenManager):
    """
    Обертка над HHTokenManager, которая:
    - сериализует параллельные обновления токена per-HR через asyncio.Lock
    - сохраняет новые токены в TokenStorage при каждом обновлении
    """

    def __init__(
        self,
        hr_id: str,
        storage: TokenStorage,
        settings: HHSettings,
        session: aiohttp.ClientSession,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        lock: asyncio.Lock,
    ) -> None:
        super().__init__(
            settings=settings,
            session=session,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
        self._storage = storage
        self._hr_id = hr_id
        self._lock = lock

    async def get_valid_access_token(self) -> str:  # type: ignore[override]
        async with self._lock:
            # Перед попыткой refresh синхронизируемся с актуальным состоянием из стораджа
            latest = self._storage.get(self._hr_id)
            if latest:
                # Если в хранилище токены/срок отличаются — обновим локальное состояние
                if (
                    self.access_token != latest.get("access_token")
                    or self.refresh_token != latest.get("refresh_token")
                    or float(self.expires_at) < float(latest.get("expires_at", 0))
                ):
                    self.access_token = latest["access_token"]
                    self.refresh_token = latest["refresh_token"]
                    self.expires_at = float(latest["expires_at"])

            token_before = self.access_token
            res = await super().get_valid_access_token()
            # Если токены могли обновиться — сохраняем
            if self.access_token != token_before:
                self._storage.save(
                    self._hr_id,
                    {
                        "access_token": self.access_token,
                        "refresh_token": self.refresh_token,
                        "expires_at": float(self.expires_at),
                    },
                )
            return res


async def exchange_code_for_tokens(
    session: aiohttp.ClientSession, settings: HHSettings, code: str
) -> Dict[str, Any]:
    """
    Выполняет обмен authorization_code на пару токенов напрямую через OAuth2 endpoint.
    Используется в callback, чтобы первично сохранить токены в хранилище.
    """
    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "code": code,
        "redirect_uri": settings.redirect_uri,
    }
    async with session.post(settings.token_url, data=payload) as resp:
        resp.raise_for_status()
        data = await resp.json()
        # преобразуем expires_in -> expires_at
        expires_at = time.time() + float(data.get("expires_in", 0))
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": expires_at,
        }
