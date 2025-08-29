# AuthPage

**Файл**: `src/pages/AuthPage.tsx`

## Что делает
Единая страница аутентификации с переключением между формами входа и регистрации.

## Ключевые компоненты
- **Табовая навигация** "Вход" ⟷ "Регистрация"
- **LoginForm** - форма входа (email/password)
- **SignupForm** - форма регистрации (email/password/org_name)

## Логика работы
```typescript
const [activeTab, setActiveTab] = useState<'login' | 'signup'>('login')

const handleAuthSuccess = () => {
  navigate('/dashboard')  // автоматический переход после успешной авторизации
}
```

## API интеграция
- **LoginForm** → `POST /auth/login` → устанавливает HttpOnly cookie
- **SignupForm** → `POST /auth/signup` → регистрация + автологин
- После успеха обе формы редиректят на `/dashboard`

## UX особенности
- **Responsive дизайн** с Tailwind CSS
- **HTML5 валидация** на стороне браузера (required, email type, minlength)
- **Loading состояния** с блокировкой кнопок при отправке
- **Обработка ошибок** с локализованными сообщениями
- **Автоочистка ошибок** при начале нового ввода

## Обработка ошибок
- `401` → "Неверный email или пароль"
- `404` → "Пользователь не найден"
- `Network errors` → "Ошибка сети"
- `Validation errors` → показ серверных ошибок валидации

## Где найти код
- **Страница**: `frontend/src/pages/AuthPage.tsx`
- **Формы**: `frontend/src/components/auth/`
- **Стили**: встроенные Tailwind классы
- **Тесты**: `frontend/tests/pages/AuthPage.test.tsx`