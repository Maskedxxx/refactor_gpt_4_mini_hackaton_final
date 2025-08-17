# Python HH.ru API OAuth2 Client

Этот проект представляет собой хорошо структурированное приложение на Python для взаимодействия с API HeadHunter (HH.ru) с использованием OAuth2. Он разделен на несколько независимых компонентов, демонстрируя чистый и модульный подход к архитектуре.

## Ключевые возможности

-   **Модульная архитектура**: Четкое разделение на `hh_adapter` (клиент HH API), `webapp` (FastAPI‑сервис с OAuth2 флоу и персистентным хранением токенов) и `callback_server` (демо для локального получения кода).
-   **Plugin-система LLM фич**: Новая архитектура `llm_features` позволяет легко добавлять и удалять LLM-функции без изменения основного кода.
-   **Унифицированное API для LLM**: Универсальные роуты `/features/{name}/generate` для всех LLM-фич с автоматической регистрацией.
-   **Полный цикл OAuth2**: Реализован полный поток авторизации "Authorization Code Grant".
-   **Автоматическое управление токенами**: Прозрачное обновление `access_token` с помощью `refresh_token`.
-   **Асинхронность**: Построен на `asyncio`, `aiohttp` и `FastAPI` для высокой производительности.
-   **Чистая архитектура**: Используются принципы SOLID, Dependency Injection и паттерны (Facade, Factory).
-   **Готовность к тестированию**: Включает юнит‑ и интеграционные тесты (`pytest`), а также демонстрационные точки входа для каждого компонента.
-   **Подробная документация**: Включает высокоуровневый обзор и детальное описание каждого компонента с диаграммами.

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
# venv\Scripts\activate    # Для Windows

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
```

---

## Как использовать

Проект можно запустить в трёх режимах.

### 1. Полный интеграционный сценарий (Рекомендуемый)

Этот скрипт запускает полный цикл: стартует сервер, открывает браузер для авторизации, ловит код, обменивает его на токены и делает тестовый запрос к API.

```bash
python -m examples.run_hh_auth_flow
```

### 2. WebApp (мультипользовательский сценарий)

Запускает FastAPI сервис с маршрутами `/auth/hh/start`, `/auth/hh/callback`, `/vacancies`.

```bash
python -m src.webapp
```

После запуска откройте:

```
http://localhost:8080/auth/hh/start?hr_id=hr-123&redirect_to=http%3A%2F%2Flocalhost%3A8080%2Fhealthz
```

После успешной авторизации можно вызывать:

```
curl "http://localhost:8080/vacancies?hr_id=hr-123&text=Python"

Также доступны эндпоинты готовности:

```
http://localhost:8080/healthz
http://localhost:8080/readyz
```
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

После запуска откройте:

```
http://localhost:8080/auth/hh/start?hr_id=hr-123
```

### 4. Демонстрация `callback_server`

Локальный одноразовый сервер (демо‑режим, не для прод):

```bash
python -m src.callback_server
```

### 5. Демонстрация `hh_adapter`

Мгновенно генерирует и выводит в консоль ссылку для авторизации на HH.ru.

```bash
python -m src.hh_adapter
```

### 6. Демонстрация Parsing (LLM резюме и HH вакансия)

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

### 7. LLM Features (новая модульная система)

#### A. Через унифицированное API

Все LLM-фичи доступны через универсальные роуты после запуска webapp:

```bash
# Запустить webapp
python -m src.webapp

# Получить список всех доступных фич
curl http://localhost:8080/features

# Генерация сопроводительного письма
curl -X POST http://localhost:8080/features/cover_letter/generate \
  -H "Content-Type: application/json" \
  -d '{
    "resume": {...},
    "vacancy": {...},
    "options": {"temperature": 0.4, "language": "ru"}
  }'

# GAP-анализ резюме
curl -X POST http://localhost:8080/features/gap_analyzer/generate \
  -H "Content-Type: application/json" \
  -d '{
    "resume": {...},
    "vacancy": {...},
    "options": {"analysis_depth": "full", "temperature": 0.2}
  }'
```

#### B. Через legacy примеры

Старые примеры все еще работают:

```bash
# Офлайн-режим без сети (фейковый LLM)
python -m examples.generate_cover_letter --vacancy tests/data/vacancy.json --fake-llm

# Реальный вызов LLM (нужен ключ OpenAI)
export OPENAI_API_KEY=...
python -m examples.generate_cover_letter --resume-pdf tests/data/resume.pdf --vacancy tests/data/vacancy.json

# GAP-анализ резюме
python -m examples.generate_gap_analysis --resume-pdf tests/data/resume.pdf --vacancy tests/data/vacancy.json

# Показать промпты
python -m examples.show_full_prompt --feature cover_letter
python -m examples.show_full_gap_prompt --prompt-version gap_analyzer.v1
```

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
  - `docs/architecture/components/webapp.md`
  - `docs/architecture/components/hh_adapter.md`
  - `docs/architecture/components/callback_server.md`
  - `docs/architecture/components/parser.md`
  - `docs/architecture/components/llm_cover_letter.md`
  - `docs/architecture/components/llm_gap_analyzer.md`
  - **LLM Features Framework**: `src/llm_features/README.md`
  - Деплой: `docs/architecture/components/docker.md`

Также см. правила и стиль для агентов/контрибьюторов: `AGENTS.md`, `CLAUDE.md`.
