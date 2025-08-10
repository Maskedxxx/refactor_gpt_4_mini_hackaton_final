# Docker Деплой (per‑школа)

## 1. Обзор

Этот документ описывает запуск WebApp в Docker для сценария «один контейнер = одна школа». Токены хранятся в SQLite на volume, переменные окружения задаются через `.env`.

## 2. Требования

- Docker Desktop / Docker Engine (Compose v2: команда `docker compose`)
- HH OAuth2 креды: `HH_CLIENT_ID`, `HH_CLIENT_SECRET`
- Разрешённый Redirect URI в HH: `http(s)://<host>:8080/auth/hh/callback`

## 3. Переменные окружения

Минимальный `.env` (в корне проекта):

```dotenv
HH_CLIENT_ID=...           # из кабинета HH
HH_CLIENT_SECRET=...
HH_REDIRECT_URI=http://localhost:8080/auth/hh/callback
WEBAPP_DB_PATH=/data/app.sqlite3
```

Примечания:
- `HH_REDIRECT_URI` должен 1:1 совпадать с зарегистрированным в HH.
- `WEBAPP_DB_PATH` указывает на файл в примонтированном томе для сохранности данных.

## 4. Сборка и запуск

Вариант A — docker compose (рекомендуется):

```bash
docker compose up --build
# Проверка
curl http://localhost:8080/healthz
```

Вариант B — docker run:

```bash
docker build -t hh-webapp .
docker run --rm --name hh-webapp \
  -p 8080:8080 \
  --env-file .env \
  -e WEBAPP_DB_PATH=/data/app.sqlite3 \
  -v hh_data:/data \
  hh-webapp
```

## 5. Пользовательский флоу

1) HR открывает в браузере:
```
http://localhost:8080/auth/hh/start?hr_id=hr-123
```
2) Проходит авторизацию на HH; WebApp принимает callback `/auth/hh/callback`, сохраняет токены в `/data/app.sqlite3`.
3) Клиентский запрос за данными:
```
curl "http://localhost:8080/vacancies?hr_id=hr-123&text=Python"
```

## 6. Диагностика и обслуживание

- Логи сервиса: выводятся в stdout контейнера (`docker compose logs -f webapp`).
- Проверка токенов в БД:
  - Скопировать БД наружу: `docker compose cp webapp:/data/app.sqlite3 ./app.sqlite3`
  - Посмотреть строки: `sqlite3 ./app.sqlite3 "select hr_id, datetime(expires_at,'unixepoch') from tokens;"`
- Остановка:
  - Сохранить данные: `docker compose down`
  - Полная очистка (включая том): `docker compose down -v`

## 7. Частые проблемы

- `Cannot connect to the Docker daemon`: запустите Docker Desktop/daemon.
- `docker-compose: command not found`: используйте `docker compose` (Compose v2).
- 404 на `/callback`: убедитесь, что `HH_REDIRECT_URI` указывает на `/auth/hh/callback` и совпадает с конфигурацией в HH.
- `Invalid HTTP request received`: шум от невалидных запросов браузера/системных проверок — не критично.
- `address already in use`: порт 8080 занят — измените публикацию порта (`-p 8081:8080`) и `HH_REDIRECT_URI`.

## 8. Продакшн рекомендации

- HTTPS и домен через reverse‑proxy (Nginx/Caddy, Traefik). Публикуйте сервис за прокси, меняйте `HH_REDIRECT_URI` на https.
- Резервное копирование тома с БД (`hh_data`).
- Лимиты ресурсов/перезапуски (`deploy`/`restart: always`).
- Секреты через Secret Manager/CI‑vault вместо `.env` (по возможности).
- Миграция на внешнюю БД (Postgres) при росте нагрузки; хранение `refresh_token` — шифрованно.

