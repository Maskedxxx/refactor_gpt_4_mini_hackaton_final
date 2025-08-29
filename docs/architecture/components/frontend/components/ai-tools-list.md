# AIToolsList

**Файл**: `src/components/ai/AIToolsList.tsx`

## Что делает

Переиспользуемый компонент для отображения списка доступных AI инструментов. Поддерживает два режима: preview (статичный) и interactive (кликабельный).

## Архитектура

### AI Tools Configuration
```typescript
export interface AITool {
  id: string              // backend feature name
  name: string           // display name
  description: string    // user-friendly description  
  icon: React.ReactNode  // Lucide icon
  color: string         // Tailwind color class
}

export const AI_TOOLS: AITool[] = [
  {
    id: 'cover_letter',
    name: 'Cover Letter', 
    description: 'Генерация персонализированных сопроводительных писем',
    icon: <FileText className="w-6 h-6" />,
    color: 'text-blue-600'
  },
  // ... остальные инструменты
]
```

### Component Props
```typescript
interface AIToolsListProps {
  sessionId?: string           // session context для AI tools
  onToolClick?: (toolId: string) => void  // callback при клике
  showAsButtons?: boolean      // interactive vs preview mode
  className?: string          // дополнительные стили
}
```

## Режимы работы

### 1. Preview Mode (`showAsButtons={false}`)
**Использование:** Dashboard, статичные страницы

- Статичные карточки без hover эффектов
- Только визуальное представление
- Компактный layout

```tsx
<AIToolsList showAsButtons={false} />
```

### 2. Interactive Mode (`showAsButtons={true}`)
**Использование:** CreateProjectPage Step 4, AI workspace

- Кликабельные кнопки с hover эффектами
- Scale анимация иконок при hover
- Callback при клике на инструмент
- Focus states для accessibility

```tsx
<AIToolsList 
  sessionId={session.session_id}
  onToolClick={handleAIToolClick}
  showAsButtons={true} 
/>
```

## Синхронизация с Backend

### Mapping на Backend Features
AI_TOOLS `id` соответствует backend feature names в `/features/{name}/generate`:

- `cover_letter` → `/features/cover_letter/generate`
- `gap_analyzer` → `/features/gap_analyzer/generate` 
- `interview_checklist` → `/features/interview_checklist/generate`
- `interview_simulation` → `/features/interview_simulation/generate`

### Future Enhancement
Можно загружать список из backend API `/features/` для динамической синхронизации:

```typescript
// Будущее улучшение:
useEffect(() => {
  const loadFeatures = async () => {
    const features = await apiClient.getFeatures()
    // Merge with static AI_TOOLS config
  }
}, [])
```

## UI/UX Design

### Visual Hierarchy
- **Icon**: Цветная иконка с уникальным цветом для каждого инструмента
- **Name**: Заголовок инструмента 
- **Description**: Краткое описание функциональности

### Interactive States
```scss
// Hover эффекты в interactive mode
.group:hover {
  border-color: indigo-300;
  background: indigo-50;
  
  .icon {
    transform: scale(1.1);  // Увеличение иконки
  }
}
```

### Accessibility
- Focus states с outline
- Semantic button/div элементы в зависимости от режима
- ARIA-labels для screen readers

## Интеграция

### Dashboard Integration
```tsx
// src/pages/DashboardPage.tsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
  <h2 className="text-xl font-semibold text-gray-900 mb-6">
    🤖 Доступные AI инструменты
  </h2>
  
  <AIToolsList showAsButtons={false} />
</div>
```

### CreateProjectPage Integration  
```tsx
// src/pages/CreateProjectPage.tsx - Step 4
<AIToolsList
  sessionId={wizardState.session.session_id}
  onToolClick={handleAIToolClick}
  showAsButtons={true}
  className="max-w-4xl mx-auto"
/>
```

## Benefits

### 1. DRY Principle
- Единый источник правды для AI инструментов
- Консистентный UI/UX между страницами
- Легко добавлять новые инструменты

### 2. Maintainability  
- Изменения в одном месте отражаются везде
- Типизированная конфигурация предотвращает ошибки
- Четкое разделение preview/interactive логики

### 3. Extensibility
- Легко добавить новые режимы отображения
- Поддержка кастомных callback'ов
- Гибкая система стилизации

## Future Enhancements

1. **Dynamic Loading**: Загрузка списка фич из backend API
2. **Feature Status**: Показ доступности фич (enabled/disabled)
3. **Usage Analytics**: Трекинг кликов для популярных инструментов
4. **Favorites**: Система избранных инструментов пользователя

## Где найти код
- **Компонент**: `frontend/src/components/ai/AIToolsList.tsx`
- **Usage Dashboard**: `frontend/src/pages/DashboardPage.tsx:185`
- **Usage CreateProject**: `frontend/src/pages/CreateProjectPage.tsx:490-495`

## Testing

- См. `frontend/tests/components/ai/AIToolsList.test.tsx`:
  - Preview mode: рендер 4 карточек без кликов
  - Interactive mode: клик по кнопке вызывает `onToolClick(toolId)`
