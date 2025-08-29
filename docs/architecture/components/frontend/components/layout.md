# Layout

**Файл**: `src/components/layout/Layout.tsx`

## Что делает
Общий каркас для авторизованных страниц. Включает header с навигацией, user menu и logout функциональность.

## Структура
```
┌─────────────────────────────────────────────────┐
│ Header: AI Career Tools | User Menu + Logout   │
├─────────────────────────────────────────────────┤
│ Navigation: Dashboard | Settings               │
├─────────────────────────────────────────────────┤
│                                                 │
│            {children}                          │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Props интерфейс
```typescript
interface LayoutProps {
  children: React.ReactNode
  user: User | null
}
```

## Header секция
- **Логотип**: "AI Career Tools" с иконкой
- **User Menu**: dropdown с email пользователя
- **Logout**: кнопка выхода с подтверждением

## Navigation
Навигационное меню с активным состоянием:
- **Dashboard** (`/dashboard`) - основная страница
- **Settings** (`/settings`) - будущий функционал

```typescript
// Определение активного пункта меню
const isActive = (path: string) => location.pathname === path

// Стили для активного/неактивного состояния
className={`... ${
  isActive(item.href) 
    ? 'bg-indigo-700 text-white' 
    : 'text-indigo-100 hover:bg-indigo-600'
}`}
```

## Logout логика
```typescript
const handleLogout = async () => {
  try {
    await apiClient.logout()  // POST /auth/logout
    navigate('/')             // переход на главную
  } catch (error) {
    console.error('Logout error:', error)
    navigate('/')  // даже при ошибке переходим
  }
}
```

## Responsive дизайн
- **Desktop**: полная навигация в sidebar
- **Mobile**: адаптивное меню (будущая функциональность)

## API интеграция
- **POST /auth/logout** - завершение сессии
- Использует данные пользователя из ProtectedRoute

## Использование
```tsx
// Автоматически используется в ProtectedRoute
<Layout user={user}>
  <DashboardPage />
</Layout>
```

## Где найти код
- **Компонент**: `frontend/src/components/layout/Layout.tsx`
- **Интеграция**: `frontend/src/components/auth/ProtectedRoute.tsx`
- **Стили**: встроенные Tailwind классы