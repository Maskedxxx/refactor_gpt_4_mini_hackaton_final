# ONBOARDING

Цель: дать агенту быстрый ориентир по репозиторию, порядок чтения и «ручки» (команды) для точечного изучения кода без лишнего контекста.

## First Steps

- Дерево (до 3 уровней):
  - `tree -L 3 -I "venv|.venv|node_modules|.git|__pycache__|dist|build" || find . -maxdepth 3 | grep -Ev "venv|.venv|node_modules|.git|__pycache__|dist|build" | sed 's|^\./||' | sort`
- Прочитайте `README.md` в корне: назначение, запуск, окружение.
- Затем `docs/architecture/overview.md`: контексты и общая архитектура.

## Reading Order

1) `README.md` — что это за проект, варианты запуска (venv/Docker), переменные окружения.
2) `docs/architecture/overview.md` — высокоуровневая схема и компоненты.
3) `docs/helpers/docs_map.yaml` — быстрая карта документации (пути и краткие описания).
4) `docs/architecture/components/*.md` — детали конкретного модуля/сервиса (имя файла соответствует модулю, например `llm_gap_analyzer.md`).
4) `docs/architecture/changelog.md` — последние ключевые изменения (если планируете правки — добавляйте запись).
5) Код целевого модуля — начните с файлов в `src/<module>/` и `agent_meta` (см. ниже).
6) Для демонстрации сценариев — `examples/` (скрипты генерации и проверки отдельных фич).

Примечание: в текущей структуре нет директорий `contracts/*` и `docs/architecture/adr/*`. Если в будущем добавите формальные контракты или ADR — включите их в order между (3) и (4).

## Sources of Truth

- Архитектура: `docs/architecture/overview.md`, `docs/architecture/components/*.md`.
- Изменения: `docs/architecture/changelog.md`.
- Поведение «в коде»: `tests/` (юнит и интеграционные), `examples/` (скрипты‑песочницы).
- Frontend: `docs/architecture/components/frontend.md` (+ дочерние страницы), код `frontend/src`, тесты `frontend/tests`.

## Quick Index

- `src/` — основной код backend: `auth/`, `webapp/`, `hh_adapter/`, `llm_*`, `pdf_export/`, `parsing/`, `callback_server/`.
- `frontend/` — React SPA (Vite, TS), маршрутизация и страницы.
- `docs/` — документация (architecture, helpers, onboarding).
- `tests/` — pytest (юнит/интеграция); `frontend/tests/` — Vitest.
- `examples/` — демонстрационные скрипты и сценарии.
- `.claude/` — prompts, reviews, настройки для AI‑агентов.

## Repo Handles (быстрые команды)

- Найти входные точки (CLI/сервер):
  - `rg -n "if __name__ == '__main__'|uvicorn|gunicorn|click\.command|Typer\(|FastAPI\(|flask\.|@app\.route" -S`
  - Fallback: `grep -REn "__main__|uvicorn|gunicorn|click\\.command|Typer\\(|FastAPI\\(|flask\\.|@app\\.route" src examples`
  - Фактические entrypoints в репозитории: `main.py`, `src/webapp/__main__.py`, `src/callback_server/__main__.py`, `src/hh_adapter/__main__.py`.
- Найти компоненты/слои: `rg -n "usecase|service|repository|gateway|adapter|controller|handler" -S src`
  - Fallback: `grep -REn "usecase|service|repository|gateway|adapter|controller|handler" src`
- Конфиг/секреты: `rg -n "(settings|config|.env|dotenv)" -S`
  - Fallback: `grep -REn "(settings|config|\\.env|dotenv)" .`
- Документация компонентов: `ls -1 docs/architecture/components`
- Запуск контейнеров: cм. `Dockerfile`, `docker-compose.yml` (детали — в README).
- Frontend:
  - Список страниц/сервисов фронта: `ls -1 docs/architecture/components/frontend/{pages,services,components}`
  - Быстрый старт dev‑сервера: `cd frontend && npm run dev`
  - Запуск фронтовых тестов: `cd frontend && npm run test:run`

## Components Map (из docs/architecture/components)

- `callback_server` — локальный callback-сервер для OAuth2 кода.
- `hh_adapter` — клиент HH API (OAuth2, токены, вызовы API).
- `auth` — аутентификация приложения (email+пароль, cookie‑сессии, `auth_sessions`).
- `webapp` (+ `webapp_llm_features`) — FastAPI-приложение, маршруты и интеграция LLM-фич.
- `llm_*` — фичи LLM: cover_letter, gap_analyzer, interview_checklist, interview_simulation.
- `parsing` — парсинг резюме/вакансий и подсистема LLM-промптов для парсинга.
- `pdf_export` — HTML-шаблоны и CSS-стили для PDF-отчетов, форматтеры и сервис печати.
- `frontend` — React+TypeScript приложение (Vite): страницы `AuthPage`, `DashboardPage`, защищённый роут `ProtectedRoute`, `Layout`, клиент `ApiClient`.

Кодовая структура соответствует этим компонентам в `src/` (папки `src/<component>`).

## Entrypoints и полезные директории

- CLI/демо: `examples/` — скрипты для запуска отдельных сценариев. **Основной демонстрационный скрипт — `examples/unified_demo.py`**, который показывает полный цикл работы приложения.
- Приложение: `src/webapp/__main__.py`, `src/webapp/app.py` — FastAPI.
- Авторизация: модуль `src/auth` подключается к WebApp через `include_router`. **Маршруты для OAuth-интеграции с HH.ru (`/auth/hh/*`) теперь находятся здесь (`src/auth/router.py`)**, а не в `webapp`.
- Адаптер HH: `src/hh_adapter/` — OAuth2, управление токенами, клиент HH.
- Callback: `src/callback_server/` — локальный обработчик кода авторизации (используется в `unified_demo`).
- PDF: `src/pdf_export/` — шаблоны, стили, форматтеры и сервис печати.
- Frontend (SPA):
  - Код: `frontend/src` (вход — `frontend/src/main.tsx`, маршрутизация — `frontend/src/App.tsx`).
  - Тесты: `frontend/tests` (Vitest + RTL, jsdom).
  - Документация: `docs/architecture/components/frontend.md` + подразделы (`pages/`, `components/`, `services/`).
  - Запуск: `cd frontend && npm install && npm run dev`.

## Task Navigator

- Новая фронтенд‑страница: `frontend/src/pages/*`, маршрут — `frontend/src/App.tsx`; документация — `docs/architecture/components/frontend/pages/*`.
- Новая LLM‑фича: см. `docs/architecture/components/webapp_llm_features.md`; код — `src/llm_<feature>/`, регистрация в `FeatureRegistry`, маршруты в `src/webapp`.
- PDF Export изменения: `src/pdf_export/`, документация — `docs/architecture/components/pdf_export.md`, маршруты `/features/{name}/export/pdf`.
- Изменения Auth/HH: `src/auth/*` (в т.ч. `router.py`, `hh_service.py`), документация — `docs/architecture/components/auth.md`; статус контракта — `is_connected`.
- CLI команда: `src/cli/*`, документация — `docs/architecture/components/cli.md`.

## Local Run

- Установка зависимостей: `pip install -r requirements.txt` (см. `README.md` для venv и переменных окружения).
- Docker/Compose: см. `Dockerfile`, `docker-compose.yml` и раздел запуска в `README.md`.
- Frontend: `cd frontend && npm install && npm run dev` (Vite dev server).

## Tests

- Тесты находятся в `tests/` (юнит и интеграционные):
  - покрывают `callback_server`, `hh_adapter`, `parsing`, `pdf_export`, `webapp`, а также интеграцию `llm_features`.
- Запуск: `pytest -q` (или вариант из `README.md`).
- Frontend‑тесты: `frontend/tests` — Vitest + RTL.
  - Запуск разово: `cd frontend && npm run test:run`
  - Watch/UI: `npm test` / `npm run test:ui`
  - Точечный файл: `npm run test:run -- tests/pages/DashboardPage.test.tsx`

## agent_meta в исходниках

- Рекомендация (см. CLAUDE.md): в начале каждого `.py` — блок `agent_meta` с ролью, владельцем, контрактом и интерфейсами:

  ```python
  # src/<relative/path>.py
  # --- agent_meta ---
  # role: <component>
  # owner: @backend
  # contract: <краткий контракт публичного API>
  # last_reviewed: YYYY-MM-DD
  # interfaces:
  #   - func(arg: Type) -> Ret
  # --- /agent_meta ---
  ```

- В текущем коде маркеры `agent_meta` могут отсутствовать. При изменениях публичных интерфейсов — добавляйте/обновляйте блоки `agent_meta` и синхронизируйте соответствующую документацию в `docs/architecture/components/*.md` и `docs/architecture/changelog.md`.

## Before You Change Code

- Сверьтесь с `docs/architecture/overview.md` и соответствующим `components/<module>.md` — изменения не должны расходиться с архитектурой.
- Обновите документацию компонента и `changelog.md` при значимых правках.
- Следуйте принципам из `CLAUDE.md` (contract-first, SOLID, типы PEP 484, форматирование ruff/black/isort).
- Не добавляйте тесты без явного запроса, но ориентируйтесь на имеющиеся тесты как «исполняемую спецификацию».

## Tips

- Для точечных задач начните с `docs/architecture/components/<module>.md`, затем смотрите публичные интерфейсы в `src/<module>/`.
- Используйте `examples/` для воспроизведения сценариев и быстрой проверки гипотез.
- Если интерфейс изменился — сначала обновите документацию и только потом код (contract-first).
