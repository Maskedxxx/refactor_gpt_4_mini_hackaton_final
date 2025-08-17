# Changelog

## 2025-08-17 (LLM Gap Analyzer — второй компонент в LLM Features Framework)

- **Добавлена новая фича llm_gap_analyzer:**
  - Создан полноценный GAP-анализатор резюме с использованием единой архитектуры LLM Features Framework.
  - Реализован `LLMGapAnalyzerGenerator` наследующий от `AbstractLLMGenerator[EnhancedResumeTailoringAnalysis]`.
  - Автоматическая регистрация в `FeatureRegistry` при импорте модуля.
  - Доступ через универсальное API: `POST /features/gap_analyzer/generate`.

- **Комплексная модель данных для HR анализа:**
  - Создана модель `EnhancedResumeTailoringAnalysis` в `src/models/gap_analysis_models.py`.
  - Поддержка первичного скрининга, детального анализа требований, оценки качества резюме.
  - Структурированные рекомендации по критичности (CRITICAL/IMPORTANT/DESIRED).
  - Расчётный процент соответствия и рекомендация по найму.

- **Система промптов и форматирования:**
  - Версионируемый промпт `gap_analyzer.v1` с HR методологией в 6 этапов.
  - Форматтеры для резюме и вакансий, динамические блоки для требований.
  - Интеграция анализа совпадений навыков из существующих компонентов.

- **Унификация контрактов фич:**
  - Добавлена поддержка `extra_context` в `GapAnalyzerOptions` для единообразия с `cover_letter`.
  - Интеграция `extra_context_block` в шаблоны промптов для пользовательских указаний.
  - Удалены неиспользуемые функции `build_enum_guidance` для очистки кодовой базы.

- **Примеры и демонстрация:**
  - `examples/generate_gap_analysis.py` — полный пример использования с настройками.
  - `examples/show_full_gap_prompt.py` — демонстрация сборки промптов.
  - Обновлён `.env.example` с переменными для настройки GAP-анализатора.

## 2025-08-15 (Tests: LLM Features API, Registry, Integration)

- Добавлены тесты для нового фреймворка LLM‑фич:
  - `tests/llm_features/test_features_api.py` — интеграционные тесты универсальных роутов `GET /features` и `POST /features/{name}/generate` с мок‑реестром и мок‑генератором.
  - `tests/llm_features/test_feature_registry.py` — юнит‑тесты `FeatureRegistry` (регистрация, версии, список, ошибки `FeatureNotFoundError`).
  - `tests/llm_features/test_cover_letter_integration.py` — интеграция `LLMCoverLetterGenerator` в рамках нового API (без внешней сети; моки).
- Обновлены разделы про тестирование: добавлена команда запуска только LLM‑фич `pytest -q tests/llm_features` в корневом `README.md` и расширен `tests/README.md`.

## 2025-08-15 (LLM Features Framework — plugin architecture)

- **Новая модульная архитектура для LLM-фич:**
  - Создан базовый фреймворк `src/llm_features` с абстрактными классами и системой регистрации.
  - Реализован `AbstractLLMGenerator[T]` с унифицированным workflow: plan-build-call-validate.
  - Добавлена система регистрации `FeatureRegistry` для автоматического управления фичами и версионирования.
  - Создан `BaseFeatureSettings` с поддержкой префиксов окружения через Pydantic.

- **Унифицированное API для всех LLM-фич:**
  - Добавлены универсальные роуты в webapp: `GET /features` и `POST /features/{name}/generate`.
  - Любая зарегистрированная фича доступна через одинаковый API без изменения кода webapp.
  - Поддержка версионирования фич и автоматический выбор версии по умолчанию.

- **Рефакторинг llm_cover_letter под новую архитектуру:**
  - `LLMCoverLetterGenerator` теперь наследует от `AbstractLLMGenerator[EnhancedCoverLetter]`.
  - Сохранена полная обратная совместимость с `ILetterGenerator` интерфейсом.
  - Автоматическая регистрация в `FeatureRegistry` при импорте модуля.
  - Обновлены настройки с префиксом `COVER_LETTER_` и наследованием от `BaseFeatureSettings`.

- **Документация для расширения:**
  - Создано подробное руководство `src/llm_features/README.md` для junior инженеров.
  - Пошаговые инструкции по созданию новых фич с полными примерами кода.
  - Обновлена архитектурная документация с диаграммами и процессами использования.

- **Готовность к росту:** Архитектура позволяет легко добавлять новые фичи (llm_gap_analyzer, llm_interview_checklist, llm_interview_simulation) без изменения основного кода.

## 2025-08-15 (HR methodology & enhanced formatter)

- **Промпт-система:**
  - Обновлен шаблон `cover_letter.v2` с полной HR методологией (3 этапа создания письма: персонализация, доказательства ценности, структура).
  - Добавлены обязательные критерии качества (✅/❌) и требования к избеганию шаблонности.
  - Улучшены descriptions полей Pydantic модели `EnhancedCoverLetter` с конкретными HR требованиями.
  - Увеличен лимит `opening_hook` с 300 до 500 символов для историй успеха с цифрами.
  - Устранено дублирование в `PersonalizationStrategy` (удален `company_knowledge`).

- **Форматтер и аналитика:**
  - Полностью переработан `formatter.py` с детальными секциями (карьерная история, языковые компетенции, сертификаты).
  - Добавлены новые функции анализа: `analyze_skills_match()`, `analyze_candidate_positioning()`, `format_cover_letter_context()`.
  - Интегрирован контекстный анализ в промпт через новую секцию "### Анализ соответствия:" в templates v2.
  - LLM теперь получает анализ совпадающих/недостающих навыков и уровня позиционирования (Junior/Middle/Senior).

- **Интеграция:** Аналитические функции автоматически интегрированы в `DefaultPromptBuilder` через передачу объектов резюме/вакансии в контексте.

## 2025-08-14 (Docs polish: path headers, env, refs)

- Зафиксировано правило: первая строка — относительный путь к файлу; добавлено в `AGENTS.md` и `CLAUDE.md`.
- Добавлены переменные `COVER_LETTER_*` в `.env.example` (версия промпта, температура, язык, проверки, модель).
- Добавлены `OPENAI_API_KEY` и `OPENAI_MODEL_NAME` (опц.) в `.env.example`.
- README: добавлена ссылка на `components/llm_cover_letter.md` в разделе архитектуры.
- Changelog: запись про Cover Letter (2025‑08‑10) поднята наверх для видимости.
- Проставлены относительные пути в шапках файлов `src/llm_cover_letter/*`.

## 2025-08-14 (Prompts: dynamic blocks, v2, extra_context)

- Подсистема промптов для Cover Letter расширена:
  - Добавлены динамические блоки: `company_tone_instruction` и `role_adaptation_instruction` (см. `prompts/mappings.py`).
  - Реализовано автоопределение `role_hint` по `resume.title` (ключевые слова в `ROLE_DETECTION_KEYWORDS`).
  - Добавлен шаблон `cover_letter.v2` с более строгими требованиями к качеству.
  - Обновлен `cover_letter.v1` (структурированные секции контекста, тональности и адаптации).
- В `DefaultPromptBuilder` восстановлена передача `options.extra_context` в `extra_context_block` (dict → маркированный список).
- Добавлен `src/llm_cover_letter/prompts/README.md` с детальным описанием сборки промпта и примерами.
- Добавлен `examples/show_full_prompt.py` для демонстрации финального System/User промптов.

## 2025-08-10 (LLM Cover Letter module — contract-first)

- Добавлен библиотечный компонент `src/llm_cover_letter`:
  - Публичный контракт: `ILetterGenerator`, `CoverLetterOptions`, модели письма.
  - Версионируемая система промптов и билдеров (`prompts/*`).
  - Сервис `LLMCoverLetterGenerator` с DI (LLM, билдеры, валидатор, настройки).
  - Валидатор качества и форматтеры блоков резюме/вакансии и email‑текста.
- Документация:
  - Новый файл `docs/architecture/components/llm_cover_letter.md`.
  - Обновлён `overview.md`, добавлена секция в README с примерами.
- Примеры: `examples/generate_cover_letter.py` (офлайн/онлайн режимы).

## 2025-08-10 (Parsing docs, demo & webapp headers)

- Компонент Parser: добавлены sequenceDiagram диаграммы потоков (резюме и вакансия) в `docs/architecture/components/parser.md`.
- Обзор архитектуры: `overview.md` дополнен компонентом `src/parsing` с ссылкой на подробности.
- README: добавлена секция демонстрации парсинга и ссылка на документацию компонента; указаны команды запуска с реальным LLM и офлайн.
- WebApp: во все файлы пакета `src/webapp/*` добавлены относительные пути в шапку перед блоком `agent_meta`.
- Без изменения контрактов и кода логики; только документация и метаданные.

## 2025-08-10 (Tests & concurrency fix for WebApp)

- Добавлены асинхронные интеграционные тесты FastAPI (`tests/webapp`):
  - `/auth/hh/start` и `/auth/hh/callback` (мок обмена кода на токены, одноразовый `state`, сохранение токенов в SQLite).
  - Конкурентные запросы к `/vacancies` с истёкшим `access_token` (пер‑HR `asyncio.Lock`, единичный refresh под нагрузкой).
- Исправлена гонка при обновлении токена: `PersistentTokenManager.get_valid_access_token` синхронизирует состояние из `TokenStorage` под пер‑HR локом перед решением о refresh и сохраняет обновлённые токены обратно.
- Документация тестов: добавлены `tests/README.md` и `tests/webapp/README.md` (что/как/зачем, изоляция окружения, TTL `state`).
- Обновлён корневой `README.md`: ссылки на `docs/architecture/*`, упоминание `/healthz`/`/readyz`, параметр `WEBAPP_DB_PATH`, пояснение про TTL `state`.
- Зависимости: добавлен `httpx>=0.27` для ASGI‑клиента в тестах.

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
