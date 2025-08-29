# API Client

**Файл**: `src/lib/api.ts`

## Что делает
Централизованный HTTP клиент для всего взаимодействия с backend API. Обрабатывает авторизацию, HH.ru интеграцию и ошибки.

## Основные методы

### Авторизация
```typescript
async login(credentials: LoginRequest): Promise<AuthResponse>
async signup(data: SignupRequest): Promise<AuthResponse>
async logout(): Promise<void>
async getCurrentUser(): Promise<User>
```

### HH.ru интеграция  
```typescript
async getHHStatus(): Promise<{ is_connected: boolean; expires_in_seconds?: number }>
async connectToHH(): Promise<void>  // redirect to HH OAuth
```

## Конфигурация
```typescript
class ApiClient {
  private client = axios.create({
    baseURL: 'http://localhost:8080',
    withCredentials: true,  // автоматическая отправка HttpOnly cookies
    headers: { 'Content-Type': 'application/json' }
  })
}

export const apiClient = new ApiClient()  // singleton instance
```

## Обработка ошибок

### Response Interceptor
Автоматический редирект при 401 (если не на странице авторизации):
```typescript
this.client.interceptors.response.use(
  response => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname
      if (currentPath !== '/' && currentPath !== '/auth') {
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  }
)
```

### Error Handler
Универсальная обработка ошибок с локализованными сообщениями:
```typescript
private handleError(error: any): Error {
  if (error.code === 'ERR_NETWORK') {
    return new Error('Ошибка сети. Проверьте подключение к интернету.')
  }
  
  const status = error.response?.status
  switch (status) {
    case 401: return new Error('Неверный email или пароль')
    case 404: return new Error('Пользователь не найден')
    case 409: return new Error('Пользователь уже существует')
    default: return new Error(error.response?.data?.detail || 'Произошла ошибка')
  }
}
```

## HH.ru интеграция особенности

### OAuth Flow
```typescript
async connectToHH(): Promise<void> {
  try {
    const response = await this.client.get('/auth/hh/connect')
    if (response.data?.auth_url) {
      window.location.href = response.data.auth_url  // redirect to HH
    }
  } catch (error: any) {
    if (error.response?.status === 409) {
      throw error  // "already connected" - обрабатывается в UI
    }
    throw new Error('Не удалось подключиться к HH.ru')
  }
}
```

### Status Check
```typescript
async getHHStatus(): Promise<HHStatus> {
  const response = await this.client.get('/auth/hh/status')
  return response.data  // { is_connected: boolean, expires_in_seconds?: number }
}
```

## Backend Endpoints
| Method | Endpoint | Назначение |
|--------|----------|-----------|
| POST | `/auth/login` | Авторизация пользователя |
| POST | `/auth/signup` | Регистрация пользователя |
| POST | `/auth/logout` | Завершение сессии |
| GET | `/me` | Информация о текущем пользователе |
| GET | `/auth/hh/status` | Статус подключения HH.ru |
| GET | `/auth/hh/connect` | Инициация OAuth с HH.ru |

## Session Management
- **HttpOnly cookies** с session ID устанавливаются backend'ом
- **Автоматическая отправка** cookies с каждым запросом (`withCredentials: true`)
- **Автоматический logout** при 401 ошибках

## Где найти код
- **API клиент**: `frontend/src/lib/api.ts`
- **Типы**: встроенные TypeScript интерфейсы
- **Тесты**: `frontend/tests/lib/api.test.ts`