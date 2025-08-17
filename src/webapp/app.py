# src/webapp/app.py
# --- agent_meta ---
# role: webapp-fastapi
# owner: @backend
# contract: FastAPI сервис с роутами /auth/hh/start, /auth/hh/callback, /vacancies
# last_reviewed: 2025-08-10
# interfaces:
#   - FastAPI app
#   - GET /auth/hh/start
#   - GET /auth/hh/callback
#   - GET /vacancies
# dependencies:
#   - FastAPI, aiohttp, sqlite3
# --- /agent_meta ---

import asyncio
import time
from typing import Dict, Optional

import aiohttp
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse

from src.hh_adapter.config import HHSettings
from src.hh_adapter.client import HHApiClient
from src.webapp.storage import TokenStorage, OAuthStateStore
from src.webapp.service import PersistentTokenManager, exchange_code_for_tokens
from src.webapp.features import router as features_router

# Импортируем модуль для автоматической регистрации фич
import src.llm_cover_letter  # Автоматически регистрирует cover_letter фичу
import src.llm_gap_analyzer  # Автоматически регистрирует gap_analyzer фичу


app = FastAPI(title="HH Adapter WebApp", version="0.1.0")

# Подключаем роуты для LLM-фич
app.include_router(features_router)


# Простые DI-синглтоны (per-process) для демо/atomarного сервиса
_settings = HHSettings()
_tokens = TokenStorage()
_state = OAuthStateStore()
_locks: Dict[str, asyncio.Lock] = {}


def _get_lock(hr_id: str) -> asyncio.Lock:
    if hr_id not in _locks:
        _locks[hr_id] = asyncio.Lock()
    return _locks[hr_id]


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.get("/auth/hh/start")
def auth_start(
    hr_id: str = Query(..., description="Идентификатор HR пользователя"),
    redirect_to: Optional[str] = Query(None, description="Куда вернуть пользователя после авторизации"),
):
    # Создаем state и редиректим на HH authorize
    state = _state.create(hr_id=hr_id, redirect_to=redirect_to)
    auth_url = (
        "https://hh.ru/oauth/authorize?response_type=code"
        f"&client_id={_settings.client_id}"
        f"&redirect_uri={_settings.redirect_uri}"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url, status_code=302)


@app.get("/auth/hh/callback")
async def auth_callback(code: str, state: str):
    consumed = _state.consume(state)
    if not consumed:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    hr_id = consumed["hr_id"]
    redirect_to = consumed.get("redirect_to")

    async with aiohttp.ClientSession() as session:
        try:
            tokens = await exchange_code_for_tokens(session, _settings, code)
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")

    _tokens.save(hr_id, tokens)

    html = "<h1>Авторизация успешна</h1><p>Можно закрыть вкладку.</p>"
    # Если указали redirect_to — перенаправим
    if redirect_to:
        return RedirectResponse(url=str(redirect_to), status_code=302)
    return HTMLResponse(content=html, status_code=200)


@app.get("/vacancies")
async def vacancies(hr_id: str, text: str = Query("", description="Строка поиска")):
    record = _tokens.get_record(hr_id)
    if not record:
        raise HTTPException(status_code=401, detail="HR not authorized")

    # Восстанавливаем менеджер токенов из стораджа
    expires_in = max(0, int(float(record.expires_at) - time.time()))
    async with aiohttp.ClientSession() as session:
        manager = PersistentTokenManager(
            hr_id=hr_id,
            storage=_tokens,
            settings=_settings,
            session=session,
            access_token=record.access_token,
            refresh_token=record.refresh_token,
            expires_in=expires_in,
            lock=_get_lock(hr_id),
        )
        client = HHApiClient(_settings, manager, session)
        try:
            data = await client.request("vacancies", params={"text": text} if text else None)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
        return JSONResponse(content=data)
