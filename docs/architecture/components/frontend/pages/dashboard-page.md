# DashboardPage

**Файл**: `src/pages/DashboardPage.tsx`

## Что делает
Главная страница после авторизации. Показывает статус HH.ru подключения, quick actions и preview AI инструментов.

## Основные секции

### 1. Welcome Hero
Приветственная секция с кнопкой "Создать новый анализ"

### 2. Quick Actions Panel
- **"Новый проект"** → `/project/create` (будущий роут)
- **"История проектов"** → `/projects` (будущий роут)

### 3. HH.ru Status Card
**Статус подключения с цветовой индикацией:**
- 🔴 **Красная кнопка** "❌ Подключить HH.ru" - не подключен
- 🟢 **Зеленая кнопка** "✅ HH.ru подключен" - подключен (disabled)

### 4. AI Tools Preview
Превью доступных инструментов:
- Cover Letter, Gap Analyzer, Interview Checklist, Interview Simulation

## HH.ru интеграция

### API вызовы
```typescript
// При загрузке страницы
const status = await apiClient.getHHStatus()  // GET /auth/hh/status

// При клике "Подключить"
await apiClient.connectToHH()  // GET /auth/hh/connect → redirect to HH OAuth
```

### Обработка статусов
```typescript
interface HHStatus {
  is_connected: boolean
  expires_in_seconds?: number  
  connected_at?: number
}
```

### 409 "Already Connected" обработка
При получении 409 ошибки (HH уже подключен):
1. Автоматически устанавливаем `is_connected: true`
2. UI мгновенно переключается на зеленую кнопку
3. Дополнительно обновляем статус с сервера

## State Management
```typescript
const [hhStatus, setHhStatus] = useState<HHStatus | null>(null)
const [hhLoading, setHhLoading] = useState(true)

// Auto-refresh при возврате на вкладку
useEffect(() => {
  const handleFocus = () => refreshHHStatus()
  document.addEventListener('visibilitychange', handleFocus)
  window.addEventListener('focus', handleFocus)
})
```

## UX особенности
- **Автообновление статуса** при возврате на вкладку
- **Кнопка 🔄** для ручного обновления статуса
- **Loading индикаторы** при запросах к API
- **Responsive дизайн** (sidebar на больших экранах)

## Где найти код
- **Страница**: `frontend/src/pages/DashboardPage.tsx`
- **Layout**: `frontend/src/components/layout/Layout.tsx`
- **API клиент**: `frontend/src/lib/api.ts`