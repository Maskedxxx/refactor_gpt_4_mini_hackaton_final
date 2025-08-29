# AI Career Tools Frontend

React SPA для системы анализа резюме и карьерных инструментов на базе AI.

## Что есть сейчас

✅ **Авторизация**: Login/Signup формы с валидацией и обработкой ошибок  
✅ **Dashboard**: Главная страница после авторизации  
✅ **HH.ru интеграция**: OAuth подключение с цветовой индикацией статуса  
✅ **Защищенные роуты**: Автоматическая проверка сессии и редирект  
✅ **Layout**: Header с навигацией, user menu и logout  
✅ **Comprehensive тесты**: Vitest + React Testing Library  

## Технологический стек

- **React 18** + **TypeScript** + **Vite**
- **React Router** - навигация между страницами
- **Tailwind CSS** - утилитарные стили
- **Lucide React** - иконки  
- **Axios** - HTTP клиент с interceptors

## Быстрый старт

```bash
# Установка зависимостей
npm install

# Запуск dev сервера  
npm run dev        # http://localhost:5173

# Тестирование
npm run test       # интерактивный режим
npm run test:run   # одноразовый запуск

# Production build
npm run build      # сборка в dist/
```

## Архитектура

```
src/
├── components/
│   ├── auth/           # ProtectedRoute
│   └── layout/         # Layout с header/nav
├── pages/              # AuthPage, DashboardPage  
├── lib/                # API client
└── App.tsx             # Router setup
```

## Роутинг

- `/` или `/auth` → **AuthPage** (вход/регистрация)
- `/dashboard` → **DashboardPage** (требует авторизации)

## API интеграция

**Backend**: `http://localhost:8080`  
**Авторизация**: HttpOnly cookies с автоматическим редиректом при 401

| Endpoint | Назначение |
|----------|------------|
| `POST /auth/login` | Вход пользователя |
| `POST /auth/signup` | Регистрация |
| `POST /auth/logout` | Выход из системы |
| `GET /me` | Текущий пользователь |
| `GET /auth/hh/status` | Статус HH.ru подключения |
| `GET /auth/hh/connect` | OAuth с HH.ru |

## HH.ru интеграция

- 🔴 **Красная кнопка**: "❌ Подключить HH.ru" (не подключен)
- 🟢 **Зеленая кнопка**: "✅ HH.ru подключен" (подключен)
- **Автообновление статуса** при возврате на вкладку
- **Smart 409 handling** - автоматическое переключение UI при "already connected"

## Документация

📚 **Детальная документация**: `docs/architecture/components/frontend.md`

Включает детальное описание каждого компонента, API интеграции, тестов и архитектурных решений.

## Планы развития

- [ ] Project Creation Wizard (файл загрузка + vacancy search)
- [ ] AI Tools интерфейс (Cover Letter, Gap Analyzer, etc.)
- [ ] Results visualization и PDF export
- [ ] Advanced HH.ru features (vacancy search, resume analysis)
