# Компонент: WebApp (FastAPI)

## 1. Обзор

`WebApp` — продакшн‑ориентированный FastAPI сервис, который инкапсулирует внешний контракт OAuth2‑аутентификации с HH.ru и предоставляет API для прикладного функционала (например, чтение вакансий). Компонент предназначен для «атомарного» деплоя per‑школа (один контейнер = одна школа), но спроектирован с учётом multi‑tenant‑готовности (привязка токенов к HR, state‑защита, сериализация refresh).

Основные обязанности:
- Инициировать OAuth2 Authorization Code Flow (`/auth/hh/start`).
- Обрабатывать callback от HH и обменивать `code` на токены (`/auth/hh/callback`).
- Хранить токены per‑HR в SQLite с безопасной моделью доступа.
- Выполнять запросы к HH API от имени HR с авто‑обновлением токена (`/vacancies`).
- Предоставлять унифицированное API для LLM-фич (`/features/{name}/generate`).

## 2. Контракт (роуты)

- `GET /auth/hh/start?hr_id=<str>&redirect_to=<url>`
  - Генерирует одноразовый `state` и делает 302 redirect на `https://hh.ru/oauth/authorize`.
  - Параметры: `response_type=code`, `client_id`, `redirect_uri` (из настроек), `state`.
- `GET /auth/hh/callback?code=<str>&state=<str>`
  - Валидирует/«съедает» `state`, меняет `code`→токены, сохраняет в хранилище.
  - Возвращает HTML «успех» или 302 на `redirect_to` из `state`.
- `GET /vacancies?hr_id=<str>&text=<str>`
  - Поднимает токены HR, выполняет запрос к HH API с авто‑refresh, возвращает JSON.
- **Новые LLM Features роуты:**
  - `GET /features` — список всех доступных LLM-фич
  - `POST /features/{feature_name}/generate` — генерация через любую зарегистрированную фичу
    - Тело запроса: либо `{ session_id, options, version? }`, либо `{ resume, vacancy, options, version? }`
    - Рекомендованный путь — через `session_id` (см. ниже "Сессии")
- **Сессии и персистентность:**
  - `POST /sessions/init_upload` — инициализация сессии из сырого ввода (PDF + vacancy URL)
  - `POST /sessions/init_json` — инициализация сессии из готовых моделей (`ResumeInfo` + `VacancyInfo`)
- Технические: `GET /healthz`, `GET /readyz`.

## 3. Архитектура

```mermaid
graph TD
    A[Client / Frontend] -->|/auth/hh/start| B[WebApp]
    B -->|302 to HH| C[HH.ru OAuth2]
    C -->|redirect with code+state| B
    B -->|exchange code| C
    B -->|save tokens| D[(SQLite)]
    A -->|/vacancies| B
    B -->|API call with token| E[HH API]
    E --> B --> A
```

Компоненты:
- `app.py` — FastAPI приложение (роуты, DI одноразовых сервисов).
- `storage.py` — SQLite‑хранилища: `TokenStorage` и `OAuthStateStore` (с TTL), путь задаётся `WEBAPP_DB_PATH`.
- `service.py` — `PersistentTokenManager` (обёртка над `HHTokenManager`), сериализует refresh через `asyncio.Lock` per‑HR, сохраняет обновлённые токены.
- **`features.py`** — унифицированные роуты для LLM-фич через `FeatureRegistry`.
- **`sessions.py`** — роуты инициализации сессий (`/sessions/init_upload`, `/sessions/init_json`).
- Использует `HHSettings`, `HHApiClient`, `HHTokenManager` из `hh_adapter`.
- Использует `FeatureRegistry`, `ILLMGenerator` из `llm_features`.
 - **`storage_docs.py`** — SQLite‑хранилища резюме/вакансий/сессий: `ResumeStore`, `VacancyStore`, `SessionStore`.

## 4. Поток аутентификации

```mermaid
sequenceDiagram
    participant U as HR Пользователь
    participant FE as Клиент/Фронт
    participant WA as WebApp
    participant HH as HH.ru
    participant DB as SQLite

    FE->>WA: GET /auth/hh/start?hr_id=...
    WA->>WA: create state(hr_id, redirect_to)
    WA-->>FE: 302 Location: https://hh.ru/oauth/authorize?...&state=...
    U->>HH: Login & Consent
    HH-->>FE: 302 Location: /auth/hh/callback?code=...&state=...
    FE->>WA: GET /auth/hh/callback?code=...&state=...
    WA->>WA: validate & consume state
    WA->>HH: POST /oauth/token (authorization_code)
    HH-->>WA: access_token, refresh_token, expires_in
    WA->>DB: save(hr_id, tokens)
    WA-->>FE: HTML Success or 302 redirect_to
```

## 5. Хранение и конкурентность

- Таблица `tokens` хранит `hr_id`, `access_token`, `refresh_token`, `expires_at`.
- Таблица `oauth_state` хранит одноразовый `state` с TTL (по умолчанию 10 минут).
- Для предотвращения гонок при параллельных запросах одного HR применяется `asyncio.Lock` per‑HR в `PersistentTokenManager` (refresh выполняется ровно один раз).

### Сессии и персистентность резюме/вакансий

- Таблица `resume_docs`: `{ id, hr_id, source_hash, title, data_json, created_at }`
- Таблица `vacancy_docs`: `{ id, hr_id, source_url, source_hash, name, data_json, created_at }`
- Таблица `sessions`: `{ id, hr_id, resume_id, vacancy_id, created_at, expires_at? }`

Поведение:
- При первичной инициализации по `init_upload` или `init_json` документы сохраняются, создаётся `session_id`.
- Повторные вызовы с тем же содержанием при `reuse_by_hash=true` переиспользуют записи (без LLM/HH API).
- Все фичи затем вызываются только с `session_id`, что исключает повторный парсинг исходных данных.

Диаграмма:

```mermaid
sequenceDiagram
  participant FE as Клиент
  participant WA as WebApp
  participant DB as SQLite
  participant HH as HH API
  participant LLM as OpenAI

  FE->>WA: POST /sessions/init_upload (hr_id, pdf, url)
  WA->>WA: hash(pdf_text), extract vacancy_id
  alt not found in DB
    WA->>LLM: parse resume -> ResumeInfo
    WA->>HH: GET vacancy -> VacancyInfo
    LLM-->>WA: ResumeInfo
    HH-->>WA: VacancyInfo
    WA->>DB: save resume_docs, vacancy_docs
  else reuse
    WA->>DB: load resume_docs, vacancy_docs
  end
  WA->>DB: create session
  WA-->>FE: {session_id, ...}

  FE->>WA: POST /features/{name}/generate {session_id, options}
  WA->>DB: get session -> resume_id, vacancy_id
  WA->>DB: load resume_docs, vacancy_docs
  WA->>LLM: feature.generate(resume, vacancy)
  LLM-->>WA: Result
  WA-->>FE: Result
```

## 6. Безопасность

- `state` защищает от CSRF и связывает запрос с `hr_id` и `redirect_to`.
- Токены не логируются; рекомендуется хранить `refresh_token` шифрованно при переходе на внешнюю БД.
- HTTPS обеспечивается внешним уровнем (Ingress/Proxy). Секреты — через переменные окружения.

## 7. Конфигурация

Переменные окружения:
- `HH_CLIENT_ID`, `HH_CLIENT_SECRET`, `HH_REDIRECT_URI` — OAuth2 настройки приложения HH.
- `WEBAPP_DB_PATH` — путь к SQLite (по умолчанию `app.sqlite3`).

Пример `.env`:
```dotenv
HH_CLIENT_ID=...
HH_CLIENT_SECRET=...
HH_REDIRECT_URI=http://localhost:8080/auth/hh/callback
WEBAPP_DB_PATH=/data/app.sqlite3
```

## 8. Деплой и Docker

Минимальный сценарий деплоя per‑школа:
- Один контейнер `webapp` с пробросом 8080.
- Том для БД (`/data/app.sqlite3`) через `WEBAPP_DB_PATH`.
- Свой `.env` с HH кредами.

Поток работы в Docker:
1) HR открывает `/auth/hh/start?hr_id=...` на домене школы.
2) После авторизации HH вызывает `/auth/hh/callback` в контейнере школы.
3) Сервис сохраняет токены в volume (`/data/app.sqlite3`).
4) Клиентские запросы к `/vacancies` используют сохранённые токены; при истечении выполняется refresh под локом, и новые токены снова пишутся в БД.

## 9. Тестирование

- Юнит‑тесты адаптера — в `tests/hh_adapter/`.
- Для WebApp рекомендуется добавить интеграционные тесты роутов с `httpx.AsyncClient` (по отдельному запросу).
- Сценарии сессий покрыты тестами: `tests/webapp/test_sessions_and_features.py`, `tests/webapp/test_sessions_upload.py`.

## 10. Примеры вызовов

Инициализация сессии (сырой ввод):
```bash
curl -X POST http://localhost:8080/sessions/init_upload \
  -F hr_id=hr-123 \
  -F vacancy_url=https://hh.ru/vacancy/123456 \
  -F reuse_by_hash=true \
  -F ttl_sec=3600 \
  -F "resume_file=@tests/data/resume.pdf;type=application/pdf"
```

Инициализация сессии (готовые модели):
```bash
curl -X POST http://localhost:8080/sessions/init_json \
  -H "Content-Type: application/json" \
  -d '{"hr_id":"hr-123","resume":{...},"vacancy":{...},"reuse_by_hash":true}'
```

Запуск фичи по session_id:
```bash
curl -X POST http://localhost:8080/features/gap_analyzer/generate \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<uuid>", "options":{"temperature":0.2}}'
```
