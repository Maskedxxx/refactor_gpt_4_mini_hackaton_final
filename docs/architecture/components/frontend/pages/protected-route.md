# ProtectedRoute

**Файл**: `src/components/auth/ProtectedRoute.tsx`

## Что делает
Обертка-компонент для защиты страниц, требующих авторизации. Проверяет сессию через `/me` endpoint.

## Логика работы
```typescript
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await apiClient.getCurrentUser()  // GET /me
        setUser(userData)
      } catch (err) {
        setError(true)  // 401 или другая ошибка
      } finally {
        setLoading(false)
      }
    }
    checkAuth()
  }, [])
}
```

## Состояния компонента

### Loading
Показывает спиннер пока проверяет авторизацию
```tsx
if (loading) return <div>Loading...</div>
```

### Error (не авторизован)
Редиректит на страницу авторизации
```tsx
if (error) return <Navigate to="/auth" replace />
```

### Success (авторизован)
Оборачивает детей в Layout и передает данные пользователя
```tsx
return (
  <Layout user={user}>
    {children}
  </Layout>
)
```

## Интеграция с Layout
ProtectedRoute автоматически оборачивает защищенные страницы в Layout компонент, передавая:
- **user** данные для отображения в header
- **logout** функциональность

## API интеграция
- **GET /me** - проверка текущей сессии
- При 401 ошибке происходит автоматический редирект (через axios interceptor)

## Использование
```tsx
// В App.tsx
<Route 
  path="/dashboard" 
  element={
    <ProtectedRoute>
      <DashboardPage />
    </ProtectedRoute>
  } 
/>
```

## Где найти код
- **Компонент**: `frontend/src/components/auth/ProtectedRoute.tsx`
- **Layout**: `frontend/src/components/layout/Layout.tsx`
- **API**: `frontend/src/lib/api.ts` (getCurrentUser method)