# src/auth/oauth_utils.py
# --- agent_meta ---
# role: oauth2-utils
# owner: @backend
# contract: OAuth2 token exchange utilities
# last_reviewed: 2025-08-23
# interfaces:
#   - exchange_code_for_tokens(session, settings, code) -> dict
# --- /agent_meta ---

import time
from typing import Dict, Any

import aiohttp

from src.hh_adapter.config import HHSettings


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