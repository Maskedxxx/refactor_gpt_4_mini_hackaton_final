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

## Интеграция с HH.ru OAuth2

Помимо собственной аутентификации, модуль `auth` теперь отвечает за полную интеграцию с OAuth2 от HeadHunter. Это позволяет пользователям приложения подключать свои HH-аккаунты и выполнять действия от их имени.

### Новые эндпоинты

-   **GET `/auth/hh/status`**: Проверяет, подключен ли HH-аккаунт к текущей сессии пользователя.
    -   Out: `{ "connected": true, "account_info": { ... } }` или `{ "connected": false }`.
-   **GET `/auth/hh/connect`**: Инициирует процесс подключения. Перенаправляет пользователя на сайт HH.ru для авторизации.
-   **GET `/auth/hh/callback`**: Принимает редирект от HH.ru после успешной авторизации, обменивает `code` на токены и сохраняет их.
-   **POST `/auth/hh/disconnect`**: Отключает привязанный HH-аккаунт от профиля пользователя.

### Ключевые компоненты интеграции

-   **`HHAccountService` (`src/auth/hh_service.py`)**: Сервисный слой, инкапсулирующий логику работы с аккаунтами HH: создание, получение, обновление токенов. Использует `hh_adapter` для взаимодействия с API HH.
-   **`require_hh_connection` (`src/auth/hh_middleware.py`)**: Middleware-зависимость (dependency) для эндпоинтов FastAPI, которая требует активного и валидного подключения к HH.ru. Автоматически внедряет в запрос контекст аккаунта и обновляет токен при необходимости.
-   **`AuthStorage` (`src/auth/storage.py`)**: Слой хранения был расширен для поддержки аккаунтов HH.

## Хранилище (SQLite) - дополнено

-   `users(id, email UNIQUE, password_hash, created_at)`
-   `organizations(id, name, created_at)`
-   `memberships(user_id, org_id, role, status)`
-   `auth_sessions(id, user_id, org_id, expires_at, ua_hash, ip_hash)`
-   **`hh_accounts(id, user_id, org_id, hh_user_id, email, access_token, refresh_token, expires_at)`**: Новая таблица для хранения данных и токенов HH-аккаунтов, привязанных к пользователям системы.

## Frontend Integration

Auth Service полностью интегрирован с React Frontend приложением через HTTP API и cookie-based sessions.

### Компоненты Frontend

**Основные компоненты для аутентификации:**
- `AuthPage` - главная страница с табовой навигацией
- `LoginForm` - форма входа (email/password)
- `SignupForm` - форма регистрации (email/password/org_name)
- `ApiClient` - централизованный HTTP клиент

### Интеграция через API

**Используемые endpoints:**
```typescript
// Аутентификация
POST /auth/login    -> { email, password }
POST /auth/signup   -> { email, password, org_name }
POST /auth/logout   -> void
GET /me            -> { user: {id, email}, org_id, role }

// HH.ru интеграция через редирект
GET /auth/hh/connect  -> redirect to HH.ru
GET /auth/hh/status   -> { connected: boolean }
```

### Session Management

**Cookie-based authentication:**
- Backend устанавливает `HttpOnly` cookie `sid` при успешном login/signup
- Frontend автоматически отправляет cookies (`withCredentials: true`)
- При 401 ошибке Frontend автоматически редиректит на `/auth`

**Автоматическая обработка авторизации:**
```typescript
// Axios interceptor в ApiClient
this.client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Редирект только если не на странице авторизации
      if (!window.location.pathname.includes('/auth')) {
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  }
)
```

### Error Handling

**Локализованные сообщения ошибок:**
- `401/Unauthorized` → "Неверный email или пароль"
- `404` → "Пользователь не найден"  
- `Network Error` → "Ошибка сети. Проверьте подключение к интернету"
- Прочие → Исходное сообщение или generic fallback

### User Experience

**UX паттерны:**
- Автоочистка ошибок при начале ввода пользователя
- Loading states во время запросов с disabled кнопками
- HTML5 валидация для базовых проверок (email format, required fields)
- Responsive дизайн с Tailwind CSS

**Workflow:**
1. Пользователь заполняет форму входа/регистрации
2. Frontend отправляет запрос с credentials к Auth Service
3. При успехе Auth Service устанавливает session cookie
4. Frontend получает подтверждение и перенаправляет пользователя
5. Все последующие запросы автоматически аутентифицированы через cookie

## Будущее расширение

-   MFA (TOTP), magic-link, SSO (OIDC/SAML), SCIM, роли и политики на уровне организации.
-   Поддержка нескольких HH-аккаунтов на одного пользователя.
-   **Frontend расширения**: Dashboard для управления организациями, профиль пользователя, управление HH.ru подключениями через UI.
