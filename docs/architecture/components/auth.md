# docs/architecture/components/auth.md

## Назначение

Аутентификация/авторизация приложения (не путать с OAuth2 HH). Простое MVP для B2B (онлайн‑школы): email+пароль, серверные cookie‑сессии, 1 организация по умолчанию на пользователя.

## Контракты API

- POST `/auth/signup` — регистрация пользователя и дефолтной организации; авто‑логин.
  - In: `{ email, password, org_name? }`
  - Out: `{ user: {id, email}, org_id }`
- POST `/auth/login` — вход, установка cookie `sid`.
  - In: `{ email, password }`
  - Out: `{ ok: true }`
- POST `/auth/logout` — выход, инвалидация сессии, очистка cookie.
  - Out: `{ ok: true }`
- GET `/me` — профиль и текущая организация/роль.
  - Out: `{ user: {id, email}, org_id, role }`
- POST `/orgs` — создать новую организацию текущим пользователем (он — `org_admin`).
  - In: `name` (query/form/json — простой строковый параметр)
  - Out: `{ org_id }`

Cookie: `sid` (`HttpOnly`, `Secure` — по `AUTH_COOKIE_SECURE`, `SameSite` — по `AUTH_COOKIE_SAMESITE`).

## Хранилище (SQLite)

- `users(id, email UNIQUE, password_hash, created_at)`
- `organizations(id, name, created_at)`
- `memberships(user_id, org_id, role, status)` — PK `(user_id, org_id)`
- `auth_sessions(id, user_id, org_id, expires_at, ua_hash, ip_hash)`

## Встраивание

Модуль атомарный, подключается в `src/webapp/app.py` через `include_router(auth_router)` и использует `WEBAPP_DB_PATH`.
Важно: `auth_sessions` не пересекается с таблицей `sessions`, которую использует подсистема документных/LLM‑сессий.

## Логирование и ошибки

- Логирование: используется общий механизм из `src/utils.py`; добавлены логи для регистрации, входа, ошибок и операций с сессиями/организациями.
- Ошибки: модульные исключения в `src/auth/exceptions.py` (например, `UserExistsError`, `InvalidCredentialsError`), которые преобразуются в структурированные HTTP‑ответы (4xx для пользовательских ошибок, 5xx для системных).

## Пример запуска

См. пример: `python -m examples.run_auth_demo --base-url http://localhost:8080`.

## Будущее расширение

- MFA (TOTP), magic‑link, SSO (OIDC/SAML), SCIM, роли и политики на уровне организации.
