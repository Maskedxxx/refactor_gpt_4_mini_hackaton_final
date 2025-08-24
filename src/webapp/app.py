# src/webapp/app.py
# --- agent_meta ---
# role: webapp-fastapi
# owner: @backend
# contract: FastAPI сервис с основными роутами (OAuth перенесен в auth/router.py)
# last_reviewed: 2025-08-23
# interfaces:
#   - FastAPI app
#   - GET /healthz
#   - GET /readyz
# dependencies:
#   - FastAPI, aiohttp, sqlite3
# --- /agent_meta ---

from fastapi import FastAPI

from src.webapp.features import router as features_router
from src.webapp.sessions import router as sessions_router
from src.webapp.pdf import router as pdf_router
from src.auth import router as auth_router

# Импортируем модули для автоматической регистрации LLM фич
import src.llm_cover_letter  # Автоматически регистрирует cover_letter фичу
import src.llm_gap_analyzer  # Автоматически регистрирует gap_analyzer фичу
import src.llm_interview_checklist  # Автоматически регистрирует interview_checklist фичу
import src.llm_interview_simulation  # Автоматически регистрирует interview_simulation фичу


app = FastAPI(title="HH Adapter WebApp", version="0.1.0")

# Подключаем роуты для LLM-фич
app.include_router(auth_router)
app.include_router(features_router)
app.include_router(sessions_router)
app.include_router(pdf_router)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


# LEGACY OAuth роуты удалены - теперь используются новые роуты в auth/router.py:
# - GET /auth/hh/connect (заменяет /auth/hh/start)  
# - GET /auth/hh/callback (интегрированный с внутренней авторизацией)
# - GET /auth/hh/status (новый функционал)
# - POST /auth/hh/disconnect (новый функционал)
# Все операции теперь работают через новую архитектуру user_id + org_id с HH авторизацией
