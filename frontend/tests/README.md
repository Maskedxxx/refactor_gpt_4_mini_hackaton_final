# Тестирование Frontend

Тестовое покрытие критических компонентов HR Assistant фронтенда.

## Структура тестов

```
tests/
├── lib/
│   └── api.test.ts            # Тесты API клиента
├── components/
│   └── auth/
│       ├── LoginForm.test.tsx  # Тесты формы входа
│       └── SignupForm.test.tsx # Тесты формы регистрации
├── pages/
│   ├── AuthPage.test.tsx      # Тесты страницы авторизации
│   └── CreateProjectPage.test.tsx  # Тесты мастера создания проекта
└── README.md                  # Этот файл
```

## Что покрыто тестами

### API Client (`lib/api.test.ts`)
- ✅ Успешная авторизация (login)
- ✅ Обработка ошибок авторизации  
- ✅ Успешная регистрация (signup)
- ✅ Обработка ошибок регистрации
- ✅ Получение информации о пользователе (getCurrentUser)
- ✅ Получение статуса HH.ru (getHHStatus)
- ✅ Обработка сетевых ошибок

### LoginForm Component (`components/auth/LoginForm.test.tsx`)
- ✅ Рендеринг формы со всеми полями
- ✅ Обновление значений полей при вводе
- ✅ Валидация обязательных полей
- ✅ Валидация email формата
- ✅ Валидация минимальной длины пароля
- ✅ Успешная отправка формы
- ✅ Отображение состояния загрузки
- ✅ Обработка ошибок API
- ✅ Очистка ошибок при новом вводе

### SignupForm Component (`components/auth/SignupForm.test.tsx`)
- ✅ Рендеринг формы со всеми полями (включая org_name)
- ✅ Обновление значений полей при вводе
- ✅ Валидация всех обязательных полей
- ✅ Валидация email формата
- ✅ Валидация минимальной длины пароля
- ✅ Валидация минимальной длины названия организации
- ✅ Успешная отправка формы
- ✅ Отображение состояния загрузки
- ✅ Обработка ошибок API
- ✅ Очистка ошибок при новом вводе

### AuthPage Component (`pages/AuthPage.test.tsx`)
- ✅ Рендеринг с формой входа по умолчанию
- ✅ Переключение между формами входа и регистрации
- ✅ Редирект на `/dashboard` после успешного входа/регистрации (мокаем `useNavigate`)
- ✅ Корректные заголовки/состояние активной вкладки
- ✅ Постоянное отображение заголовка страницы

### DashboardPage (`pages/DashboardPage.test.tsx`)
- ✅ Загрузка статуса HH (loading → состояние)
- ✅ Состояния: подключен/не подключен (зелёная/красная кнопка)
- ✅ Ручное обновление статуса (кнопка "Обновить статус")
- ✅ Обработка `409 HH_ALREADY_CONNECTED` при `connectToHH` (мгновенный перевод UI в "подключен" + фоновое обновление)
- ✅ Наличие ключевых ссылок: `/project/create`, `/projects`, `/profile`

### CreateProjectPage (`pages/CreateProjectPage.test.tsx`)
- ✅ Happy‑path: HH connected → Upload (PDF + URL) → Preview → initSession → Success + AI tools
- ✅ Disconnected + 409: `connectToHH` возвращает 409 → мгновенно считаем подключённым, затем фоновой рефетч
- ✅ Ошибка подключения HH (не 409): остаёмся на Step 1, UI стабилен
- ✅ Валидации: не‑PDF файл, inline валидатор URL, доступность кнопки перехода
- ✅ FormData: `resume_file` (File name/type), `vacancy_url`, `reuse_by_hash='true'`
- ✅ Спиннеры: Step 1 (пока грузится статус), Step 3 (пока идёт initSession)

Notes:
- Для скрытого file input используем `fireEvent.change(input, { target: { files: [file] } })`.
- Для негативного кейса (не‑PDF) допустим `user.upload(..., { applyAccept: false })`, но предпочтительнее `fireEvent.change`.
- Для проверки успеха шага 4 надёжнее ждать доменные данные ответа (`resume.title`, `vacancy.name`), а не декоративные заголовки с emoji.
- После изменения формы повторно получайте элементы и используйте `findBy*`/`waitFor` для асинхронных состояний.

## Запуск тестов

```bash
# Разовый запуск всех тестов
npm run test:run

# Watch режим (перезапуск при изменениях)
npm test

# UI интерфейс для тестов
npm run test:ui

# Запуск с coverage отчетом
npm run test:coverage

# Запуск одного файла
npm run test:run -- tests/pages/DashboardPage.test.tsx

# Мастер создания проекта
npm run test:run -- tests/pages/CreateProjectPage.test.tsx

# Запуск одного теста по имени
npm run test:run -- tests/pages/DashboardPage.test.tsx -t "manual refresh"
```

## Технологии

- **Vitest** — быстрый тестовый раннер совместимый с Vite
- **React Testing Library** — тестирование React компонентов с фокусом на UX
- **jsdom** — эмуляция браузерного окружения для Node.js
- **@testing-library/user-event** — симуляция пользовательских действий

## Принципы тестирования

1. **User-centric тестирование** — тесты взаимодействуют с компонентами как реальный пользователь
2. **Behavioral testing** — фокус на поведении, а не на реализации
3. **Error scenarios** — обязательное покрытие error handling
4. **Loading states** — тестирование состояний загрузки
5. **Form validation** — полное покрытие валидации форм

### Специфика file input и асинхронности
- Скрытые inputs: `fireEvent.change` надёжнее `userEvent.upload`.
- `findBy*` и `waitFor`: используйте для появления/исчезновения текстов ошибок и смены disabled.

### Устойчивость тестов (guidelines)
- По возможности используйте `role`/`label` вместо точных текстов.
- Для спорных элементов допускается `title`/`data-testid` как стабильный якорь (например, кнопка обновления HH).
- Изменения контрактов (роуты, поля API — напр. `is_connected`) требуют осознанного обновления тестов.

## Что не покрыто (пока)

- E2E тесты полного flow авторизации  
- Visual regression тесты
- Performance тесты
- Accessibility тесты
- Router navigation тесты

> Тесты покрывают все критические сценарии текущего функционала и обеспечивают уверенность в стабильности приложения.
