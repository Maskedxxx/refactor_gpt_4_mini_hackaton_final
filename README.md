# Python HH.ru API OAuth2 Client

Этот проект представляет собой хорошо структурированное приложение на Python для взаимодействия с API HeadHunter (HH.ru) с использованием OAuth2. Он разделен на два независимых компонента, демонстрируя чистый и модульный подход к архитектуре.

## Ключевые возможности

-   **Модульная архитектура**: Четкое разделение на `hh_adapter` (для работы с API) и `callback_server` (для обработки OAuth2 редиректа).
-   **Полный цикл OAuth2**: Реализован полный поток авторизации "Authorization Code Grant".
-   **Автоматическое управление токенами**: Прозрачное обновление `access_token` с помощью `refresh_token`.
-   **Асинхронность**: Построен на `asyncio`, `aiohttp` и `FastAPI` для высокой производительности.
-   **Чистая архитектура**: Используются принципы SOLID, Dependency Injection и паттерны (Facade, Factory).
-   **Готовность к тестированию**: Включает юнит-тесты (`pytest`) и демонстрационные точки входа для каждого компонента.
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
```

### 3. Docker (рекомендуется для per‑школа деплоя)

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

---

## Тестирование

Проект содержит набор юнит-тестов для проверки ключевой логики. Тесты используют моки и не требуют реальных сетевых запросов.

Для запуска всех тестов выполните команду:

```bash
pytest
```

## Архитектура

Для глубокого понимания структуры проекта, принципов проектирования и взаимодействия компонентов, пожалуйста, обратитесь к [**подробной архитектурной документации**](./docs/architecture/overview.md).
