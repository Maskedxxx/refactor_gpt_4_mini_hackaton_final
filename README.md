# Python HH.ru API OAuth2 Client

Этот проект представляет собой хорошо структурированное приложение на Python для взаимодействия с API HeadHunter (HH.ru) с использованием OAuth2. Он разделен на несколько независимых компонентов, демонстрируя чистый и модульный подход к архитектуре.

## Ключевые возможности

-	**Модульная архитектура**: Четкое разделение на `hh_adapter` (клиент HH API), `webapp` (FastAPI‑сервис с OAuth2 флоу и персистентным хранением токенов) и `callback_server` (демо для локального получения кода).
-	**4 LLM-фичи для HR процессов**: Cover Letter, GAP-анализ резюме, Interview Checklist, многораундовая Interview Simulation с AI HR-менеджером.
-	**Комплексная PDF Export система**: Профессиональные отчеты для всех LLM-фич с HTML шаблонами и CSS стилизацией.
-	**Plugin-система LLM фич**: Новая архитектура `llm_features` позволяет легко добавлять и удалять LLM-функции без изменения основного кода.
-	**Унифицированное API для LLM**: Универсальные роуты `/features/{name}/generate` для всех LLM-фич с автоматической регистрацией.
-	**Полный цикл OAuth2**: Реализован полный поток авторизации "Authorization Code Grant".
-	**Автоматическое управление токенами**: Прозрачное обновление `access_token` с помощью `refresh_token`.
-	**Асинхронность**: Построен на `asyncio`, `aiohttp` и `FastAPI` для высокой производительности.
-	**Чистая архитектура**: Используются принципы SOLID, Dependency Injection и паттерны (Facade, Factory).
-	**Готовность к тестированию**: Включает юнит‑ и интеграционные тесты (`pytest`), а также демонстрационные точки входа для каждого компонента.
-	**Подробная документация**: Включает высокоуровневый обзор и детальное описание каждого компонента с диаграммами.

---

## Начало работы

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd refactor_gpt_4_mini_hackaton_final
```

### 2. Установка зависимостей

Рекомендуется использовать виртуальное окружение.

```bash
python -m venv venv
source venv/bin/activate  # Для macOS/Linux
# venv\\Scripts\\activate    # Для Windows

pip install -r requirements.txt
```

### 3. Настройка окружения

Создайте файл `.env` в корне проекта, скопировав `.env.example`.

```bash
cp .env.example .env
```

Заполните `.env` вашими учетными данными, полученными при регистрации приложения на [HH.ru](https://dev.hh.ru/admin):

```dotenv
# .env
HH_CLIENT_ID=ВАШ_ID_КЛИЕНТА
HH_CLIENT_SECRET=ВАШ_СЕКРЕТНЫЙ_КЛЮЧ
HH_REDIRECT_URI=http://localhost:8080/auth/hh/callback

# Примечание: локальный callback_server оставлен для демо и не требуется для WebApp
# CALLBACK_HOST=127.0.0.1
# CALLBACK_PORT=8080

# Необязательные параметры для WebApp
# WEBAPP_DB_PATH=app.sqlite3  # путь к SQLite БД (по умолчанию app.sqlite3 в корне)

# Параметры Auth (MVP)
# AUTH_COOKIE_SECURE=false     # для локалки false; в проде true
# AUTH_COOKIE_SAMESITE=lax     # lax|strict|none
# AUTH_SESSION_TTL_SEC=604800  # 7 дней
```

---

## Как использовать

Проект можно запустить в нескольких режимах.

### 1. Унифицированный демо-сценарий (Рекомендуемый)

Этот скрипт запускает полный цикл:
1.	Регистрирует/логинит пользователя.
2.	Запускает WebApp.
3.	Показывает, как инициировать подключение к HH.ru через браузер.
4.	Демонстрирует вызов LLM-фич и экспорт в PDF.

```bash
python -m examples.unified_demo
```

### 2. WebApp (основной сервис)

Запускает FastAPI сервис, который обслуживает все LLM-фичи и пользовательские сессии.

```bash
python -m src.webapp
```

После запуска WebApp, аутентификация и подключение аккаунта HH.ru происходит через следующие шаги:
1.	**Регистрация/логин пользователя** в системе (см. раздел "Auth (MVP)").
2.	**Подключение HH.ru аккаунта** через браузер. Для этого пользователь должен перейти по адресу:
	```
	http://localhost:8080/auth/hh/connect
	```
3.	После успешной авторизации на HH.ru и возврата на сайт, его сессия будет привязана к аккаунту HH.

Все последующие запросы к API, требующие данных от HH.ru (например, списка вакансий), будут автоматически использовать данные подключенного аккаунта. Контекст пользователя передается через cookie (`sid`), поэтому параметр `hr_id` больше не используется.

Пример запроса списка вакансий (после логина и подключения HH):
```
curl -b cookies.txt "http://localhost:8080/vacancies?text=Python"
```

Также доступны эндпоинты готовности:
```
http://localhost:8080/healthz
http://localhost:8080/readyz
```

Сессии и персистентность (ускоряет фичи, избегает повторных парсингов):

```bash
# Инициализация сессии из PDF и URL вакансии (требует логина)
curl -X POST http://localhost:8080/sessions/init_upload \
  -b cookies.txt \
  -F vacancy_url=https://hh.ru/vacancy/123456 \
  -F reuse_by_hash=true \
  -F "resume_file=@tests/data/resume.pdf;type=application/pdf"

# Инициализация сессии из готовых моделей (альтернатива, требует логина)
curl -X POST http://localhost:8080/sessions/init_json \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"resume":{...},"vacancy":{...}}'

# Запуск любой LLM-фичи по session_id (без повторного парсинга)
curl -X POST http://localhost:8080/features/gap_analyzer/generate \
  -H "Content-Type: application/json" \
  -d '{"session_id":"<uuid>", "options": {"temperature": 0.2}}'
```

### 3. Docker (рекомендуется для деплоя)

Быстрый запуск в Docker:

```bash
# 1) Собрать образ
docker build -t hh-webapp .

# 2) Создать .env со значениями (как выше) и задать путь БД
echo "WEBAPP_DB_PATH=/data/app.sqlite3" >> .env

# 3) Запустить контейнер с volume для БД
docker run --env-file .env -p 8080:8080 -v hh_data:/data --name hh-webapp hh-webapp

# Проверка
curl http://localhost:8080/healthz
```

С docker-compose:

```yaml
version: "3.9"
services:
  webapp:
    build: .
    image: hh-webapp:latest
    env_file: .env
    ports:
      - "8080:8080"
    environment:
      - WEBAPP_DB_PATH=/data/app.sqlite3
    volumes:
      - hh_data:/data
volumes:
  hh_data: {}
```

После запуска выполните шаги аутентификации, как описано в разделе "WebApp (основной сервис)". Для подключения HH.ru аккаунта перейдите по адресу:
```
http://localhost:8080/auth/hh/connect
```

### 4. Демонстрация `hh_adapter` (внутренний компонент)

Генерирует ссылку для авторизации на HH.ru. Теперь используется внутри `Auth` сервиса и напрямую не вызывается.

```bash
# python -m src.hh_adapter # <-- Deprecated
```

### 5. Демонстрация Parsing (LLM резюме и HH вакансия)

Пример запуска парсинга резюме из PDF (через LLM) и вакансии из локального JSON:

```bash
# Реальный вызов LLM (нужен ключ OpenAI)
export OPENAI_API_KEY=...  # опционально: OPENAI_MODEL_NAME=gpt-4o-mini-2024-07-18
python -m examples.parse_parsers --resume tests/data/resume.pdf --vacancy tests/data/vacancy.json

# Офлайн-режим без сети (фейковый LLM)
python -m examples.parse_parsers --fake-llm --resume tests/data/resume.pdf --vacancy tests/data/vacancy.json
```

Подробнее о внутренних контрактах и потоках: `docs/architecture/components/parser.md`.

---

## Auth (MVP)

Встроенная аутентификация приложения (не путать с OAuth2 HH). Простая реализация для старта: email+пароль, серверные cookie‑сессии, 1 организация по умолчанию на пользователя.

- Регистрация (авто‑логин):
  ```bash
  curl -i -c cookies.txt \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"secret123","org_name":"Demo School"}' \
    http://localhost:8080/auth/signup
  ```
- Вход:
  ```bash
  curl -i -c cookies.txt -H "Content-Type: application/json" \
    -d '{"email":"admin@example.com","password":"secret123"}' \
    http://localhost:8080/auth/login
  ```
- Профиль:
  ```bash
  curl -b cookies.txt http://localhost:8080/me
  ```
- Создать организацию:
  ```bash
  curl -X POST -b cookies.txt 'http://localhost:8080/orgs?name=Another%20Org'
  ```
- Выход:
  ```bash
  curl -X POST -b cookies.txt -c cookies.txt http://localhost:8080/auth/logout
  ```

Демо‑скрипт `run_auth_demo` был объединен с `unified_demo`. Используйте его для ознакомления с полным флоу.

Конфигурация: `AUTH_COOKIE_SECURE`, `AUTH_COOKIE_SAMESITE`, `AUTH_SESSION_TTL_SEC`. Таблица сессий: `auth_sessions` (не пересекается с LLM `sessions`). Подробнее: `docs/architecture/components/auth.md`.

### 6. LLM Features (новая модульная система)

#### A. Через унифицированное API

Все LLM-фичи доступны через универсальные роуты после запуска webapp:

```bash
# Запустить webapp
python -m src.webapp

# Получить список всех доступных фич
curl http://localhost:8080/features

# Генерация сопроводительного письма (с моделями напрямую)
curl -X POST http://localhost:8080/features/cover_letter/generate \
  -H "Content-Type: application/json" \
  -d '{
    "resume": {...},
    "vacancy": {...},
    "options": {"temperature": 0.4, "language": "ru"}
  }'

# GAP-анализ резюме (через session_id)
curl -X POST http://localhost:8080/features/gap_analyzer/generate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"<uuid>", "options": {"analysis_depth": "full", "temperature": 0.2}
  }'

# Interview Checklist (через session_id или напрямую)
curl -X POST "http://localhost:8080/features/interview_checklist/generate?version=v1" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"<uuid>",
    "options": {"temperature": 0.3, "language": "ru"}
  }'

# Interview Simulation (многораундовая симуляция интервью)
curl -X POST http://localhost:8080/features/interview_simulation/generate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"<uuid>",
    "options": {"rounds": 5, "difficulty": "middle", "include_behavioral": true}
  }'

# либо без session_id (с прямыми моделями)
curl -X POST "http://localhost:8080/features/interview_checklist/generate?version=v1" \
  -H "Content-Type: application/json" \
  -d '{
    "resume": { /* ResumeInfo */ },
    "vacancy": { /* VacancyInfo */ },
    "options": {"temperature": 0.3, "language": "ru"}
  }'
```

### 7. PDF Export (экспорт отчетов)

Все LLM-фичи поддерживают экспорт в PDF формат с профессиональным оформлением:

```bash
# Экспорт результата любой фичи в PDF
curl -X POST http://localhost:8080/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "interview_simulation",
    "result": {...},
    "format_options": {"language": "ru"}
  }'

# Экспорт GAP-анализа
curl -X POST http://localhost:8080/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "gap_analyzer", 
    "result": {"screening": {...}, "requirements_analysis": {...}},
    "format_options": {"language": "ru"}
  }'

# Экспорт сопроводительного письма
curl -X POST http://localhost:8080/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "cover_letter",
    "result": {"letter_text": "...", "personalization": {...}},
    "format_options": {"language": "ru"}
  }'
```

#### B. Через legacy примеры

Старые примеры были заменены на `examples/unified_demo.py`, который демонстрирует весь функционал в одном месте.

#### C. Добавление новых фич

См. подробное руководство: `src/llm_features/README.md`

## Тестирование

Проект содержит набор юнит‑ и интеграционных тестов. Тесты используют моки и не требуют реальных сетевых запросов.

Для запуска всех тестов выполните команду:

```bash
pytest
```

Полезно:

- Запуск только webapp‑тестов: `pytest -q tests/webapp`
- Запуск только llm_features‑тестов: `pytest -q tests/llm_features`
- Подробности о тестах: см. `tests/README.md` и `tests/webapp/README.md`

Примечание про TTL: одноразовый `state` в OAuth‑флоу имеет ограниченный TTL (время жизни), по умолчанию 600 секунд. По истечении времени `state` считается недействительным и будет отклонён (см. `src/webapp/storage.py`).

## Архитектура

Для глубокого понимания структуры проекта, принципов проектирования и взаимодействия компонентов, обратитесь к документации:

- Общий обзор: `docs/architecture/overview.md`
- Компоненты:
  - `docs/architecture/components/auth.md`
  - `docs/architecture/components/webapp.md`
  - `docs/architecture/components/hh_adapter.md`
  - `docs/architecture/components/callback_server.md`
  - `docs/architecture/components/parser.md`
  - `docs/architecture/components/llm_cover_letter.md`
  - `docs/architecture/components/llm_gap_analyzer.md`
  - `docs/architecture/components/llm_interview_checklist.md`
  - `docs/architecture/components/llm_interview_simulation.md`
  - `docs/architecture/components/pdf_export.md`
  - **LLM Features Framework**: `src/llm_features/README.md`
  - Деплой: `docs/architecture/components/docker.md`

Также см. правила и стиль для агентов/контрибьюторов: `AGENTS.md`, `CLAUDE.md`.