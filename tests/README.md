# Тесты проекта — краткое руководство

Цель: дать быстрый обзор того, что именно мы проверяем, как запускать тесты и как их расширять.

Состав
- hh_adapter:
  - tests/hh_adapter/test_token_manager.py — проверяет жизненный цикл OAuth2‑токенов в HHTokenManager: возврат валидного токена, авто‑refresh истёкшего токена.
- callback_server:
  - tests/callback_server/test_code_handler.py — файл‑ориентированная логика: запись/чтение/очистка кода авторизации для демо‑callback сервера.
- llm_features:
  - tests/llm_features/test_features_api.py — универсальные REST‑роуты фич: `GET /features`, `POST /features/{name}/generate` (мок‑реестр, мок‑генератор, проверка 200/404/422/500).
  - tests/llm_features/test_feature_registry.py — реестр фич (`FeatureRegistry`): регистрация, список, версии, ошибки `FeatureNotFoundError`.
  - tests/llm_features/test_cover_letter_integration.py — интеграция `LLMCoverLetterGenerator` в новом API (без сети; моки LLM/конфигурации).
- webapp (интеграционные async‑тесты FastAPI):
  - tests/webapp/test_webapp_auth_and_storage.py — флоу `/auth/hh/start` и `/auth/hh/callback`, создание и одноразовое потребление `state`, сохранение токенов в SQLite, обработка невалидного `state`.
  - tests/webapp/test_webapp_vacancies_concurrency.py — конкурентные запросы к `/vacancies` при истёкшем токене: проверяем, что срабатывает авто‑refresh и он выполняется ровно один раз на HR (per‑HR лок + синхронизация со сторожем).

Как запускать
- Установка зависимостей: `pip install -r requirements.txt`
- Запуск всех тестов: `pytest -q`
- Только llm_features: `pytest -q tests/llm_features`
- Только webapp: `pytest -q tests/webapp`
- Запуск отдельного теста/кейса: `pytest -q tests/webapp/test_webapp_auth_and_storage.py::test_callback_exchanges_tokens_and_redirects`

Изоляция окружения
- База данных: каждый тест webapp использует временную SQLite‑БД через переменную окружения `WEBAPP_DB_PATH` (см. `tests/webapp/conftest.py`). Это гарантирует отсутствие побочных эффектов между прогонами.
- Сеть: внешние HTTP‑вызовы замоканы (patch на `exchange_code_for_tokens`, `_refresh_token`, `HHApiClient.request`), поэтому доступ в интернет не требуется.
- HH‑настройки: фикстура задаёт `HH_CLIENT_ID/HH_CLIENT_SECRET/HH_REDIRECT_URI` для стабильности.
 - LLM‑фичи: тесты `tests/llm_features` используют мок‑реестр и мок‑генераторы, сетевых вызовов нет.

Что валидируется (контракты)
- OAuth state: одноразовость и ограниченный TTL (в коде по умолчанию 600 сек; в тестах проверяем одноразовость и корректность ошибок, TTL‑тест можно добавить отдельно).
- Хранилище токенов: корректное сохранение/чтение `access_token`, `refresh_token`, `expires_at`.
- Конкурентность: один refresh при множественных параллельных запросах за счёт per‑HR `asyncio.Lock` и ресинхронизации состояния токенов из персистентного стораджа.
- Коды ответов: 2xx для успешных путей, 4xx для ошибок валидации (например, невалидный state).

Подсказки и расширение
- Предупреждение pytest‑asyncio о loop scope можно снять, задав в `pytest.ini`: `asyncio_default_fixture_loop_scope = function`.
- Дополнительно стоит покрыть:
  - TTL истечение `state` (перемотка времени/monkeypatch time.time/freezegun).
  - `/healthz` и `/readyz`.
  - Ошибки обновления токена (например, 401 от провайдера): маппинг в 401/502 на нашем REST.
  - Rate limit/backoff у HH API (через моки и ретраи).

Требования
- pytest, pytest‑asyncio, httpx (ASGITransport), aiohttp — уже включены в `requirements.txt`.
