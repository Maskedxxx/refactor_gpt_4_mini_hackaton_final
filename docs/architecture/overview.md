# Обзор архитектуры

В этом документе представлен высокоуровневый обзор архитектуры системы, включая основные компоненты и процесс аутентификации.

## Компоненты

Система состоит из нескольких компонентов и одного веб‑сервиса:

- **Frontend (`frontend/`):** React+TypeScript веб-приложение с современным интерфейсом для авторизации пользователей. Предоставляет формы входа и регистрации с валидацией, интегрируется с Auth Service через HTTP API и cookie-based sessions. Использует Tailwind CSS для стилизации и Vite для сборки. Включает comprehensive тестовое покрытие с Vitest и React Testing Library.

- **Callback Server (`src/callback_server`):** Легковесный сервер на FastAPI, отвечающий за одну задачу: перехват `authorization_code` в процессе OAuth2. Он запускается, ожидает перенаправления пользователя от провайдера аутентификации, сохраняет код во временный файл и завершает работу. Используется для локальных демонстраций.

- **WebApp (`src/webapp`):** Продакшн‑ориентированный FastAPI сервис, который предоставляет API для LLM-фич, экспорта в PDF и управления сессиями (`ResumeInfo`/`VacancyInfo`). Включает CORS middleware для интеграции с Frontend. Непосредственно аутентификацией и управлением токенами HH не занимается.

- **Auth (`src/auth`):** Модуль аутентификации и управления пользователями. Отвечает за:
  - Регистрацию и вход (email+пароль).
  - Управление сессиями через cookie (`sid`).
  - **Интеграцию с HH.ru OAuth2**: предоставляет эндпоинты `/auth/hh/connect`, `/auth/hh/callback`, `/auth/hh/status` и управляет жизненным циклом токенов HH, привязывая их к аккаунту пользователя (`user_id`, `org_id`). Для этого использует `HHAccountService`.

- **HH Adapter (`src/hh_adapter`):** Клиент для API HH.ru. Используется сервисом `Auth` для выполнения OAuth2 флоу и последующих запросов к API HH. Напрямую из `WebApp` не вызывается.

- **Parsing (`src/parsing`):** Библиотечный модуль без собственного сервиса. Решает две задачи: извлечение информации из резюме (PDF → LLM → `ResumeInfo`) и преобразование вакансий из HH JSON в `VacancyInfo`. Подробности и диаграммы см. в `docs/architecture/components/parser.md`.
 
- **LLM Features Framework (`src/llm_features`):** Модульная архитектура для LLM-фич с автоматической регистрацией, версионированием и унифицированным API. Включает базовые классы (`AbstractLLMGenerator`), систему регистрации (`FeatureRegistry`) и универсальные роуты (`/features/{name}/generate`). Подробности: `src/llm_features/README.md`.

- **LLM Cover Letter (`src/llm_cover_letter`):** Первая фича в новой архитектуре. Генерация персонализированных сопроводительных писем из `ResumeInfo` и `VacancyInfo` с использованием LLM и версионируемой системы промптов. См. `docs/architecture/components/llm_cover_letter.md`.

- **LLM Gap Analyzer (`src/llm_gap_analyzer`):** Вторая фича в LLM Features Framework. Детальный GAP-анализ соответствия резюме вакансии с использованием профессиональной HR методологии (6 этапов: скрининг, анализ требований, оценка качества, рекомендации). Генерирует структурированный анализ с процентом соответствия и рекомендацией по найму. Поддерживает PDF экспорт. См. `docs/architecture/components/llm_gap_analyzer.md`.

- **PDF Export (`src/pdf_export`):** Модульная система экспорта результатов LLM-фич в PDF формат. Использует WeasyPrint + Jinja2 для рендеринга HTML шаблонов с профессиональными CSS стилями. Поддерживает все зарегистрированные фичи через систему форматтеров. Интегрирован с WebApp API. См. `docs/architecture/components/pdf_export.md`.

- **LLM Interview Checklist (`src/llm_interview_checklist`):** Третья фича. Генерация профессионального чек-листа подготовки к интервью (технический/поведенческий блоки, исследование компании, приоритеты, ресурсы, критерии успеха). Доступна через универсальное API (`/features/interview_checklist/generate`), поддерживает версионирование и экспорт в PDF.

- **LLM Interview Simulation (`src/llm_interview_simulation`):** Четвёртая фича. Полноценная симуляция интервью между AI HR-менеджером и AI кандидатом на основе реального резюме и вакансии. Адаптивные вопросы под уровень кандидата (junior/middle/senior/lead), многораундовый диалог, покрытие различных типов вопросов (технические, поведенческие, мотивационные), полный трейсинг и профессиональный PDF экспорт. Доступна через API (`/features/interview_simulation/generate`) и CLI. См. `docs/architecture/components/llm_interview_simulation.md`.

- **CLI (`src/cli`):** Консольный интерфейс для взаимодействия с WebApp API. Обеспечивает полный доступ к функционалу системы через командную строку с персистентной аутентификацией (session cookies), загрузкой документов, генерацией всех LLM-фич и конфигурируемыми опциями. Включает специальные конфигурации для симуляции интервью с детальными настройками сложности, стиля HR и типов вопросов.

## Процесс аутентификации

Диаграмма ниже иллюстрирует процесс HH OAuth (подключение провайдера). Для входа в приложение используется `src/auth` (cookie‑сессии), что отделено от HH OAuth.

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant WebApp as WebApp (FastAPI)
    participant Auth as Auth Service
    participant HH as HH.ru API

    User->>WebApp: /me (с cookie sid)
    WebApp->>Auth: require_user (middleware)
    Auth-->>WebApp: User(id, org_id)

    User->>WebApp: Клик на "Подключить HH.ru"
    WebApp->>User: 302 Redirect на /auth/hh/connect

    User->>+Auth: GET /auth/hh/connect
    Auth->>HH: Сгенерировать Auth URL
    Auth-->>User: 302 Redirect на HH.ru

    User->>+HH: Войти и предоставить доступ
    HH-->>-User: Redirect на /auth/hh/callback?code=...

    User->>+Auth: GET /auth/hh/callback?code=...
    Auth->>Auth: Проверить state, обменять code на токены
    Auth->>Auth: Сохранить/обновить HHAccount (привязка к user_id)
    Auth-->>-User: 302 Redirect на страницу профиля

    User->>WebApp: GET /vacancies?text=Python (с cookie sid)
    WebApp->>Auth: require_hh_connection (middleware)
    Auth->>Auth: Загрузить HHAccount для пользователя
    Auth->>HH: Запрос к API с токеном
    HH-->>Auth: Данные
    Auth-->>WebApp: Данные
    WebApp-->>User: JSON с вакансиями
```

## LLM Features Architecture

Новая модульная архитектура для LLM-функций обеспечивает легкое добавление и удаление фич:

```mermaid
graph TB
    API["/features/{name}/generate"] --> Registry[FeatureRegistry]
    PDF_API["/features/{name}/export/pdf"] --> PDFService[PDFExportService]
    
    Registry --> CoverLetter[LLMCoverLetterGenerator]
    Registry --> GapAnalyzer[LLMGapAnalyzerGenerator]
    Registry --> Interview[LLMInterviewChecklistGenerator]
    Registry --> Future[Future Features...]
    
    CoverLetter --> Base[AbstractLLMGenerator]
    GapAnalyzer --> Base
    Future --> Base
    
    Base --> LLM[LLM Client]
    Base --> Prompt[Prompt Builder]
    Base --> Validator[Quality Validator]
    
    PDFService --> GAFormatter[GapAnalyzerPDFFormatter]
    PDFService --> CLFormatter[CoverLetterPDFFormatter]
    PDFService --> ICFormatter[InterviewChecklistPDFFormatter]
    PDFService --> FutureFormatter[Future Formatters...]
    
    GAFormatter --> Templates[HTML Templates]
    CLFormatter --> Templates
    Templates --> WeasyPrint[WeasyPrint + CSS]
    
    subgraph "Implemented Features"
        CoverLetter
        GapAnalyzer
        CoverLetter -.-> CL_Model[EnhancedCoverLetter]
        GapAnalyzer -.-> GA_Model[EnhancedResumeTailoringAnalysis]
        Interview
        Interview -.-> IC_Model[ProfessionalInterviewChecklist]
    end
    
    subgraph "PDF Export System"
        PDFService
        GAFormatter
        CLFormatter
        ICFormatter
        Templates
        WeasyPrint
    end
    
    subgraph "Base Framework"
        Base
        Registry
        LLM
        Prompt
        Validator
    end
    
    subgraph "Future Features"
        Future
        Interview[Interview Checklist]
        Simulation[Interview Simulation]
        FutureFormatter
    end
```

### Процесс использования LLM фич

```mermaid
sequenceDiagram
    participant Client
    participant WebApp
    participant Registry as FeatureRegistry
    participant Feature as LLMGenerator
    participant LLM as OpenAI

    Client->>WebApp: POST /features/{name}/generate (session_id | resume+vacancy)
    WebApp->>Registry: get_generator(name)
    Registry-->>WebApp: LLMGenerator instance
    WebApp->>Feature: generate(resume, vacancy, options)
    Feature->>Feature: _build_prompt()
    Feature->>LLM: generate_structured()
    LLM-->>Feature: Structured Result
    Feature->>Feature: validate() [optional]
    Feature-->>WebApp: Result
    WebApp-->>Client: JSON Response
```

### Сессии и персистентность

Добавлена лёгкая подсистема сессий для одного «первого касания», после которого все фичи вызываются только с `session_id`:

```mermaid
sequenceDiagram
  participant Client
  participant WebApp
  participant DB as SQLite
  participant HH as HH API
  participant LLM as OpenAI

  Client->>WebApp: POST /sessions/init_upload (pdf + url)
  alt найдено по хэшам
    WebApp->>DB: load ResumeInfo/VacancyInfo
  else
    WebApp->>LLM: parse resume(pdf)
    WebApp->>HH: load vacancy(url)
    LLM-->>WebApp: ResumeInfo
    HH-->>WebApp: VacancyInfo
    WebApp->>DB: save docs
  end
  WebApp->>DB: create session
  WebApp-->>Client: session_id

  Client->>WebApp: POST /features/{name}/generate {session_id}
  WebApp->>DB: fetch session -> docs
  WebApp->>LLM: generate feature
  WebApp-->>Client: Result
```
