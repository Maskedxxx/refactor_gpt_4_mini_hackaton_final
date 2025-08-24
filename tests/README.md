# Тесты проекта — краткое руководство

Цель: дать быстрый обзор того, что именно мы проверяем, как запускать тесты и как их расширять.

## Состав

- **hh_adapter:**
  - `tests/hh_adapter/test_token_manager.py` — проверяет жизненный цикл OAuth2‑токенов в `HHTokenManager`: возврат валидного токена, авто‑refresh истёкшего токена.
- **callback_server:**
  - `tests/callback_server/test_code_handler.py` — файл‑ориентированная логика: запись/чтение/очистка кода авторизации для демо‑callback сервера.
- **llm_features:**
  - `tests/llm_features/test_features_api.py` — универсальные REST‑роуты фич: `GET /features`, `POST /features/{name}/generate`.
  - `tests/llm_features/test_feature_registry.py` — реестр фич (`FeatureRegistry`): регистрация, список, версии, ошибки.
  - `tests/llm_features/test_cover_letter_integration.py` — интеграция `LLMCoverLetterGenerator` в новом API.
  - `tests/llm_features/test_interview_checklist_integration.py` — интеграция `LLMInterviewChecklistGenerator`.
- **webapp (интеграционные async‑тесты FastAPI):**
  - `tests/webapp/test_sessions_and_features.py` — JSON‑инициализация сессии (`/sessions/init_json`), дедуп по хэшам, запуск фич по `session_id`.
  - `tests/webapp/test_sessions_upload.py` — multipart‑инициализация (`/sessions/init_upload`) из PDF+URL; дедуп до внешних вызовов.
- **auth (интеграционные тесты авторизации и HH OAuth):**
  - `tests/auth/test_auth.py` — покрывает основной флоу регистрации и логина: `/auth/signup`, `/auth/login`, `/auth/logout`, `/me`, `/orgs`.
  - `tests/auth/test_hh_account_service.py` — юнит-тесты для `HHAccountService`, проверяющие логику работы с токенами HH в изоляции.
  - `tests/auth/test_hh_oauth_integration.py` — интеграционные тесты полного цикла HH OAuth: `/auth/hh/connect`, `/auth/hh/callback`, `/auth/hh/status`, `/auth/hh/disconnect`.
  - `tests/auth/test_oauth_states_storage.py` — тесты для хранилища состояний OAuth, включая проверку TTL.

## Как запускать

- Установка зависимостей: `pip install -r requirements.txt`
- Запуск всех тестов: `pytest -q`
- Только llm_features: `pytest -q tests/llm_features`
- Только webapp: `pytest -q tests/webapp`
- Только auth: `pytest -q tests/auth`
- Запуск отдельного теста/кейса: `pytest -q tests/auth/test_hh_oauth_integration.py::test_full_oauth_flow`

## PDF экспорт

- Тесты для PDF экспорта находятся в `tests/pdf_export`.
- Запуск только PDF‑тестов: `pytest -q tests/pdf_export`

## Изоляция окружения

- **База данных:** каждый тест использует временную SQLite‑БД, что гарантирует отсутствие побочных эффектов.
- **Сеть:** внешние HTTP‑вызовы замоканы, поэтому доступ в интернет не требуется.
- **Настройки:** фикстуры задают все необходимые переменные окружения.

## Что валидируется (контракты)

- **OAuth state:** одноразовость и ограниченный TTL (проверяется в `tests/auth/test_oauth_states_storage.py`).
- **Хранилище токенов HH:** корректное сохранение, чтение и обновление токенов, привязанных к `user_id` (проверяется в `tests/auth/test_hh_account_service.py`).
- **Интеграция HH OAuth:** полный цикл от редиректа на HH до получения токенов и проверки статуса.
- **Коды ответов:** 2xx для успешных путей, 4xx для ошибок валидации.
- **Сессии:** дедупликация по хэшу контента резюме и `vacancy_id`.

## Подсказки и расширение

- Предупреждение `pytest-asyncio` о `loop scope` можно снять, задав в `pytest.ini`: `asyncio_default_fixture_loop_scope = function`.
- Дополнительно стоит покрыть ошибки обновления токена, rate-limiting и TTL у сессий.