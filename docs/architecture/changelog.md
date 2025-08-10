# Changelog

## 2025-08-10 (WebApp for multi-user OAuth2)

-   Added `src/webapp` FastAPI service with routes `/auth/hh/start`, `/auth/hh/callback`, `/vacancies` for production use.
-   Implemented SQLite-based `TokenStorage` and `OAuthStateStore` (per-school container pattern).
-   Added `PersistentTokenManager` wrapper with per-HR `asyncio.Lock` to serialize refresh.
-   Updated `docs/architecture/overview.md` to reflect WebApp flow; `callback_server` marked as demo-only.
-   Added `docs/architecture/components/webapp.md` and `docs/architecture/components/docker.md` with run/ops details.
-   Updated Docker artifacts (`Dockerfile`, `docker-compose.yml` without deprecated version key).

## 2025-08-05 (Project Scaffolding & DX)

-   **Added `README.md`:** Created a comprehensive root `README.md` with a project overview, setup instructions, and usage examples for all run modes.
-   **Added Component Demos:** Implemented `__main__.py` entry points for both `hh_adapter` and `callback_server` to allow for independent demonstration and testing.
-   **Added Unit Tests:**
    -   Set up `pytest` with `pytest-asyncio` and `pytest-mock`.
    -   Added critical unit tests for `CodeFileHandler` (file operations) and `HHTokenManager` (token refresh logic).
-   **Improved Project Structure:**
    -   Added `src/callback_server/__init__.py` to define the component's public API.
    -   Added `agent_meta` blocks to all new test and demo files for clarity.
-   **Enhanced Documentation:** Updated component-specific markdown files (`hh_adapter.md`, `callback_server.md`) with new sections on testing and standalone execution.

## 2025-08-04 (Observability, Documentation & Metadata)

-   **Улучшено логирование:**
    -   Добавлено комплексное логирование во все компоненты `hh_adapter` и `callback_server` для улучшения наблюдаемости и упрощения отладки OAuth2 флоу.
    -   Реализовано маскирование конфиденциальных данных (client_id, токенов) в логах.
-   **Улучшена документация:**
    -   Добавлены подробные docstrings в стиле Google для всех компонентов с описанием архитектурных паттернов (Facade, Factory, DAO), примерами использования и рекомендациями по безопасности.
-   **Улучшены метаданные:**
    -   Обновлены `agent_meta` во всех файлах: уточнены роли, контракты переведены на русский язык, добавлены зависимости и используемые паттерны проектирования.


## 2025-07-25 (Fixes for review: .claude/reviews/2025-07-25_hh_adapter_final_review.md)

-   **Addressed final review feedback:**
    -   `src/hh_adapter/tokens.py`: Refined comments to explain *why* logic exists, not *what* it does, adhering to `CLAUDE.md` standards.
    -   `src/callback_server/config.py`: Unified naming by changing `local_host`/`local_port` to `host`/`port` for consistency.
    -   `.env.example`: Updated variable names to `CALLBACK_HOST`/`CALLBACK_PORT` to match config changes.
    -   `src/callback_server/manager.py`: Updated code to use the new `host`/`port` setting names.

## 2025-07-25 (Developer Experience & Refactoring)

-   **Refactored project structure for clarity:**
    -   `main.py`: Cleaned up to serve as a future main application entry point.
    -   `examples/run_hh_auth_flow.py`: Created a new example script from the old `main.py` to demonstrate the HH.ru authentication flow.
-   **Improved configuration loading:**
    -   `src/hh_adapter/config.py`, `src/callback_server/config.py`: Refactored settings models (`HHSettings`, `CallbackServerSettings`) to be self-contained, loading their own variables from `.env` using an `env_prefix`.
    -   `src/config.py`: Updated `AppSettings` to use `Field(default_factory=...)` for robust initialization of nested settings.
-   **Added development helpers:**
    -   `examples/run_hh_auth_flow.py`: Introduced a `USE_MOCK_AUTH` flag to allow testing the application logic without requiring a real OAuth2 authorization flow.
-   **Improved code clarity:**
    -   `src/hh_adapter/*`: Added inline comments to clarify implementation details in the `auth`, `tokens`, and `client` modules.

## 2025-07-24 (Final Refactoring for review: .claude/reviews/2025-07-24_hh_adapter_follow_up_review.md)

-   **Architectural Refactoring (DIP & SRP):**
    -   `src/config.py`: Removed global `settings` instance to enforce Dependency Injection.
    -   `main.py`: Created a single entry point for the application, responsible for initializing `AppSettings`.
    -   `src/hh_adapter/*`: Reverted modules to accept `HHSettings` via their constructors.
    -   `src/callback_server/manager.py`: Created `ServerManager` to encapsulate server lifecycle logic.
    -   `src/callback_server/code_handler.py`: Created `CodeFileHandler` to isolate file system operations.
-   **Security & Reliability Enhancements:**
    -   `src/callback_server/server.py`: Replaced `os.kill` with a graceful shutdown mechanism using `asyncio.Event`.
    -   `src/hh_adapter/tokens.py`, `src/hh_adapter/client.py`: Added `try...except` blocks to handle `aiohttp.ClientError` and introduced custom exceptions (`HHTokenError`, `HHApiError`).
-   **Documentation Updates:**
    -   `src/hh_adapter/__init__.py`: Corrected `agent_meta` to accurately list all exported classes.

## 2025-07-24 (Docs #4)

-   **Updated architecture documentation:**
    -   `docs/architecture/overview.md`: Reworked the file to include the `callback_server` component and added a Mermaid sequence diagram for the complete authentication flow.
    -   `docs/architecture/components/hh_adapter.md`: Updated the `Overview` section to clarify the dependency on an external module (like `callback_server`) for obtaining the initial authorization code.

## 2025-07-24 (Feature #3)

-   **Added local callback server for OAuth2 flow:**
    -   `src/utils.py`: Created new file with `init_logging_from_env()` and `get_logger()`.
    -   `src/callback_server/config.py`: Created `CallbackServerSettings` model.
    -   `src/callback_server/server.py`: Created FastAPI `app` with `/callback` endpoint to save the authorization code to a file and shut down.
    -   `src/callback_server/main.py`: Created `run_server_and_wait_for_code()` to manage the server lifecycle.
    -   `src/config.py`: Updated `AppSettings` to include `callback_server: CallbackServerSettings`.
    -   `.env.example`: Added `CALLBACK_LOCAL_HOST` and `CALLBACK_LOCAL_PORT` variables.
    -   `.gitignore`: Added `.auth_code` to ignored files.

## 2025-07-24 (Fixes for review: .claude/reviews/2025-07-24_hh_adapter_review.md)

-   **Addressed architectural review feedback:**
    -   `src/hh_adapter/api.py`: Deleted the file to remove role duplication.
    -   `src/hh_adapter/tokens.py`: Corrected typing to `Dict[str, Any]`.
    -   `src/hh_adapter/config.py`: Removed the global `settings` instance.
-   **Corrected subsequent implementation errors:**
    -   `src/hh_adapter/auth.py`, `tokens.py`, `client.py`: Fixed `Undefined name 'settings'` by adding correct imports.
    -   Added file path comments to all Python files.
    -   Updated `agent_meta` in all module files to include class names.
-   **Configured environment variables:**
    -   `.env.example`: Created the file to serve as a template.
    -   `.gitignore`: Created the file to exclude `.env`.

## 2025-07-24 (Initial Implementation)

-   **Refactored and created `hh_adapter` component:**
    -   `src/config.py`: Created `BaseAppSettings`.
    -   `src/hh_adapter/config.py`: Created `HHSettings`.
    -   `src/hh_adapter/tokens.py`: Created `HHTokenManager` class.
    -   `src/hh_adapter/client.py`: Created `HHApiClient` class.
    -   `src/hh_adapter/auth.py`: Created `HHAuthService` class.
    -   `src/hh_adapter/__init__.py`: Updated public exports.
-   **Initialized project structure:**
    -   Created directories `src/hh_adapter` and `docs/architecture/components`.
    -   Created `docs/architecture/components/hh_adapter.md` and `docs/architecture/changelog.md`.
