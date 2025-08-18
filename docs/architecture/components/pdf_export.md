# Компонент: PDF Export

## 1. Обзор

`PDF Export` — модульная система экспорта результатов LLM-фич в профессиональный PDF формат. Компонент обеспечивает единообразный подход к генерации PDF отчетов для всех зарегистрированных фич в LLM Features Framework.

Основные обязанности:
- Экспорт структурированных результатов LLM-фич в PDF формат
- Рендеринг HTML шаблонов с профессиональными CSS стилями
- Модульная архитектура с поддержкой новых фич через форматтеры
- Интеграция с WebApp API через унифицированные роуты
- Обеспечение консистентного дизайна всех PDF отчетов

## 2. Архитектура

```mermaid
graph TD
    A[Client Request] --> B[WebApp /pdf/generate]
    B --> C[PDFExportService]
    C --> D[Formatter Registry]
    D --> E{Feature Type}
    
    E -->|gap_analyzer| F[GapAnalyzerPDFFormatter]
    E -->|cover_letter| G[CoverLetterPDFFormatter]
    E -->|future_feature| H[Future Formatters...]
    
    F --> I[prepare_context]
    G --> I
    H --> I
    
    I --> J[HTML Template]
    J --> K[Jinja2 Rendering]
    K --> L[CSS Styling]
    L --> M[WeasyPrint]
    M --> N[PDF Output]
```

## 3. Компоненты

### 3.1 PDFExportService (`src/pdf_export/service.py`)

Основной сервис для генерации PDF документов:

```python
class PDFExportService:
    async def generate_pdf(
        self, 
        feature_name: str, 
        data: Dict[str, Any], 
        metadata: Dict[str, Any]
    ) -> bytes
```

**Обязанности:**
- Управление реестром форматтеров
- Координация процесса генерации PDF
- Обработка ошибок и валидация данных
- Настройка WeasyPrint для корректного рендеринга

### 3.2 AbstractPDFFormatter (`src/pdf_export/formatters/base.py`)

Базовый класс для всех форматтеров фич:

```python
class AbstractPDFFormatter(ABC):
    @property
    @abstractmethod
    def feature_name(self) -> str
    
    @property
    @abstractmethod
    def template_name(self) -> str
    
    @abstractmethod
    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]
```

**Контракт:**
- `feature_name` — идентификатор фичи для регистрации
- `template_name` — имя HTML шаблона (например, `gap_analyzer.html`)
- `prepare_context()` — преобразование данных фичи в контекст для шаблона

### 3.3 Реализованные форматтеры

#### GapAnalyzerPDFFormatter (`src/pdf_export/formatters/gap_analyzer.py`)

Форматтер для GAP анализа резюме:

**Секции PDF:**
- Мета-информация (дата генерации, версия)
- Первичный скрининг с индикаторами
- Детальный анализ требований
- Оценка качества резюме
- Рекомендации по улучшению (критические, важные, опциональные)
- Итоговая сводка с процентом соответствия

**Ключевые методы:**
- `_translate_*()` — перевод enum значений в человекочитаемый текст
- `_get_*_css_class()` — CSS классы для визуальных индикаторов
- Обработка списков рекомендаций и требований

#### CoverLetterPDFFormatter (`src/pdf_export/formatters/cover_letter.py`)

Форматтер для сопроводительных писем:

**Секции PDF:**
- Мета-информация о роли и компании
- Анализ соответствия навыков
- Стратегия персонализации
- Полный текст письма (структурированно)
- Оценки качества письма
- Рекомендации по улучшению

**Особенности:**
- Форматирование дат и времени
- Обработка многострочного текста письма
- Прогресс-бары для оценок качества

## 4. Шаблоны и стили

### 4.1 HTML шаблоны (`src/pdf_export/templates/`)

Каждая фича имеет свой шаблон:
- `gap_analyzer.html` — профессиональный анализ с таблицами
- `cover_letter.html` — структурированное письмо с секциями

**Структура шаблона:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        {% include 'base.css' %}
        {% include 'feature_specific.css' %}
    </style>
</head>
<body>
    <div class="container">
        <!-- Feature-specific content -->
    </div>
</body>
</html>
```

### 4.2 CSS стили (`src/pdf_export/styles/`)

**Базовые стили (`base.css`):**
- Общие стили для всех PDF (шрифты, отступы, контейнеры)
- Утилитарные классы для статусов и индикаторов
- Responsive дизайн для PDF формата

**Фича-специфичные стили:**
- `gap_analyzer.css` — стили для анализа (таблицы требований, статусы)
- `cover_letter.css` — стили для письма (секции, прогресс-бары)

**Цветовая схема:**
- Зеленый (#28a745) — положительные статусы
- Красный (#dc3545) — критические проблемы
- Желтый (#ffc107) — предупреждения
- Синий (#007bff) — информационные элементы

## 5. API интеграция

### 5.1 WebApp роуты (`src/webapp/pdf.py`)

```python
@router.post("/generate")
async def generate_pdf(request: PDFGenerateRequest) -> Response
```

**Запрос:**
```json
{
    "feature_name": "gap_analyzer",
    "data": { /* результат фичи */ },
    "metadata": {
        "feature_name": "gap_analyzer",
        "version": "v1",
        "generated_at": "2025-08-17T10:00:00"
    }
}
```

**Ответ:**
- Content-Type: `application/pdf`
- Binary PDF content
- Filename header для скачивания

### 5.2 Примеры использования

**Генерация PDF через API:**
```bash
curl -X POST http://localhost:8080/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "feature_name": "gap_analyzer",
    "data": {...},
    "metadata": {...}
  }' \
  --output report.pdf
```

**Интеграция с фичами:**
```python
# 1. Генерируем результат фичи
result = await generator.generate(resume, vacancy, options)

# 2. Экспортируем в PDF
pdf_content = await pdf_service.generate_pdf(
    feature_name="gap_analyzer",
    data=result.model_dump(),
    metadata={"feature_name": "gap_analyzer", "version": "v1"}
)
```

## 6. Workflow интеграция

### 6.1 Полный workflow

```mermaid
sequenceDiagram
    participant User
    participant WebApp
    participant LLMGen as LLM Generator
    participant PDFService as PDF Service
    participant WeasyPrint

    User->>WebApp: POST /features/{name}/generate
    WebApp->>LLMGen: generate(resume, vacancy, options)
    LLMGen-->>WebApp: Feature Result
    
    User->>WebApp: POST /pdf/generate
    WebApp->>PDFService: generate_pdf(feature_name, data)
    PDFService->>PDFService: get_formatter(feature_name)
    PDFService->>PDFService: prepare_context(data)
    PDFService->>WeasyPrint: render_html_to_pdf
    WeasyPrint-->>PDFService: PDF bytes
    PDFService-->>WebApp: PDF content
    WebApp-->>User: PDF download
```

### 6.2 CLI примеры

Существующие примеры поддерживают PDF workflow:

**GAP анализ:**
```bash
# Генерируем и сохраняем результат
python examples/generate_gap_analysis.py --save-result --fake-llm

# Тестируем PDF генерацию
python examples/test_pdf_export.py --feature gap_analyzer
```

**Cover Letter:**
```bash
# Генерируем и сохраняем результат
python examples/generate_cover_letter.py --save-result --fake-llm

# Тестируем PDF генерацию
python examples/test_pdf_export.py --feature cover_letter
```

## 7. Расширение под новые фичи

### 7.1 Добавление нового форматтера

1. **Создать форматтер:**
```python
# src/pdf_export/formatters/new_feature.py
class NewFeaturePDFFormatter(AbstractPDFFormatter):
    @property
    def feature_name(self) -> str:
        return "new_feature"
    
    @property  
    def template_name(self) -> str:
        return "new_feature.html"
    
    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        # Преобразование данных для шаблона
        return {...}
```

2. **Создать шаблон:**
```html
<!-- src/pdf_export/templates/new_feature.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        {% include 'base.css' %}
        {% include 'new_feature.css' %}
    </style>
</head>
<body>
    <!-- Контент фичи -->
</body>
</html>
```

3. **Создать стили:**
```css
/* src/pdf_export/styles/new_feature.css */
.new-feature-specific {
    /* Стили специфичные для фичи */
}
```

4. **Зарегистрировать в сервисе:**
```python
# src/pdf_export/service.py или src/webapp/pdf.py
from .formatters.new_feature import NewFeaturePDFFormatter

_formatters_registry = {
    "gap_analyzer": GapAnalyzerPDFFormatter(),
    "cover_letter": CoverLetterPDFFormatter(),
    "new_feature": NewFeaturePDFFormatter(),  # Добавить здесь
}
```

### 7.2 Лучшие практики

**Дизайн:**
- Используйте базовые CSS классы для консистентности
- Следуйте цветовой схеме существующих форматтеров
- Тестируйте PDF в разных браузерах и PDF просмотрщиках

**Производительность:**
- Оптимизируйте размер CSS (избегайте дублирования)
- Используйте эффективные селекторы
- Кэшируйте статические ресурсы при необходимости

**Тестирование:**
- Создавайте unit тесты для форматтеров
- Добавляйте integration тесты для PDF генерации
- Тестируйте с реальными данными фич

## 8. Технические детали

### 8.1 Зависимости

- **WeasyPrint** — рендеринг HTML в PDF
- **Jinja2** — шаблонизация HTML
- **CSS3** — стилизация для печати

### 8.2 Настройки WeasyPrint

```python
HTML(string=html_content).write_pdf(
    stylesheets=[],
    optimize_images=True,
    presentational_hints=True
)
```

### 8.3 Обработка ошибок

- `ValueError` — неизвестная фича или некорректные данные
- `TemplateNotFound` — отсутствует HTML шаблон
- `WeasyPrint errors` — ошибки рендеринга PDF

## 9. Тестирование

### 9.1 Структура тестов

```
tests/pdf_export/
├── conftest.py              # Общие фикстуры
├── test_formatters.py       # Unit тесты форматтеров
├── test_integration.py      # Integration тесты сервиса
└── test_e2e.py             # End-to-end тесты workflow
```

### 9.2 Типы тестов

**Unit тесты:**
- Тестирование `prepare_context()` методов
- Проверка translation методов
- Валидация CSS классов

**Integration тесты:**
- Полная генерация PDF из данных
- Проверка размера и валидности PDF
- Тестирование обработки ошибок

**End-to-end тесты:**
- Workflow от генерации фичи до PDF
- Тестирование через WebApp API
- Работа с реальными сохраненными данными

### 9.3 Запуск тестов

```bash
# Все PDF тесты
python -m pytest tests/pdf_export/ -v

# Только unit тесты
python -m pytest tests/pdf_export/test_formatters.py -v

# Только integration тесты
python -m pytest tests/pdf_export/test_integration.py -v
```

## 10. Мониторинг и метрики

### 10.1 Логирование

- Генерация PDF с указанием фичи и размера
- Ошибки рендеринга с деталями
- Время выполнения генерации

### 10.2 Метрики производительности

- Время генерации PDF по фичам
- Размер генерируемых PDF файлов
- Частота ошибок рендеринга

### 10.3 Алерты

- Превышение времени генерации
- Высокий процент ошибок
- Проблемы с шаблонами или стилями