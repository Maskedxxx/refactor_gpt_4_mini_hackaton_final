# LLM Features Framework 🚀

Модульная архитектура для создания LLM-фич с автоматической регистрацией, версионированием и унифицированным API.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Архитектура](#архитектура)
- [Создание новой фичи](#создание-новой-фичи)
- [Контракт фичи](#контракт-фичи)
- [Конфигурация](#конфигурация)
- [API Integration](#api-integration)
- [Примеры](#примеры)
- [Troubleshooting](#troubleshooting)

## 🚀 Быстрый старт

### Что такое LLM Feature?

**LLM Feature** — это модуль, который:
- Принимает резюме (`ResumeInfo`) и вакансию (`VacancyInfo`)
- Генерирует через LLM какой-то полезный результат
- Имеет свои настройки, промпты и версии

**Реализованные фичи:**
- `cover_letter` — генерация персонализированных сопроводительных писем
- `gap_analyzer` — детальный GAP-анализ соответствия резюме вакансии с HR методологией

**Планируемые фичи:**
- `interview_checklist` — чеклист для подготовки к собеседованию
- `interview_simulation` — симуляция интервью

### Как это работает?

1. **Создаешь фичу** → наследуешь от `AbstractLLMGenerator`
2. **Регистрируешь** → автоматически появляется в API
3. **Используешь** → `POST /features/{название}/generate`

## 🏗 Архитектура

```
src/llm_features/               # 🏠 Базовая архитектура
├── base/
│   ├── generator.py            # AbstractLLMGenerator - базовый класс
│   ├── interfaces.py           # ILLMGenerator - контракт
│   ├── options.py              # BaseLLMOptions - базовые настройки
│   └── errors.py               # Исключения
├── registry.py                 # FeatureRegistry - управление фичами
├── config.py                   # BaseFeatureSettings - конфигурация
└── prompts/
    └── versioning.py           # Система версионирования промптов

src/llm_your_feature/           # 📦 Ваша фича
├── __init__.py                 # Экспорты и автоматическая регистрация
├── service.py                  # YourFeatureGenerator
├── models.py                   # Модели результата
├── options.py                  # YourFeatureOptions
├── config.py                   # YourFeatureSettings
└── bootstrap.py                # Регистрация в реестре

src/webapp/features.py          # 🌐 Универсальное API
└── POST /features/{name}/generate
```

## 🔨 Создание новой фичи

### Шаг 1: Создаем структуру

```bash
mkdir src/llm_your_feature
cd src/llm_your_feature
touch __init__.py service.py models.py options.py config.py bootstrap.py
```

### Шаг 2: Определяем модель результата (`models.py`)

```python
# src/llm_your_feature/models.py
from pydantic import BaseModel, Field

class YourFeatureResult(BaseModel):
    \"\"\"Результат работы вашей фичи.\"\"\"
    
    summary: str = Field(description=\"Краткое резюме\")
    recommendations: list[str] = Field(description=\"Список рекомендаций\")
    score: float = Field(ge=0.0, le=1.0, description=\"Оценка от 0 до 1\")
```

### Шаг 3: Создаем опции (`options.py`)

```python
# src/llm_your_feature/options.py
from typing import Literal
from pydantic import Field
from src.llm_features.base.options import BaseLLMOptions

class YourFeatureOptions(BaseLLMOptions):
    \"\"\"Опции для вашей фичи.\"\"\"
    
    # Переопределяем дефолты
    temperature: float = Field(default=0.2, description=\"Температура для вашей фичи\")
    
    # Добавляем специфичные настройки
    analysis_depth: Literal[\"surface\", \"deep\"] = Field(
        default=\"surface\", 
        description=\"Глубина анализа\"
    )
```

### Шаг 4: Создаем конфигурацию (`config.py`)

```python
# src/llm_your_feature/config.py
from pydantic import Field, ConfigDict
from src.llm_features.config import BaseFeatureSettings

class YourFeatureSettings(BaseFeatureSettings):
    \"\"\"Настройки из environment переменных.\"\"\"
    
    # Специфичные дефолты
    temperature: float = Field(default=0.2, description=\"Температура\")
    analysis_depth: str = Field(default=\"surface\", description=\"Глубина анализа\")
    
    model_config = ConfigDict(
        env_file=\".env\",
        env_prefix=\"YOUR_FEATURE_\",  # Префикс для env переменных
        extra=\"ignore\"
    )
```

### Шаг 5: Реализуем генератор (`service.py`)

```python
# src/llm_your_feature/service.py
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.prompt import Prompt
from src.llm_features.base.generator import AbstractLLMGenerator
from src.llm_features.base.options import BaseLLMOptions

from .models import YourFeatureResult
from .options import YourFeatureOptions
from .config import YourFeatureSettings

class YourFeatureGenerator(AbstractLLMGenerator[YourFeatureResult]):
    \"\"\"Генератор вашей фичи.\"\"\"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._settings = YourFeatureSettings()
    
    async def _build_prompt(
        self, 
        resume: ResumeInfo, 
        vacancy: VacancyInfo, 
        options: BaseLLMOptions
    ) -> Prompt:
        \"\"\"Строим промпт для вашей фичи.\"\"\"
        system = f\"\"\"
        Ты эксперт по анализу резюме и вакансий.
        Температура: {options.temperature}
        Глубина анализа: {getattr(options, 'analysis_depth', 'surface')}
        \"\"\"
        
        user = f\"\"\"
        Резюме: {resume.title} 
        Вакансия: {vacancy.name}
        
        Проанализируй соответствие и дай рекомендации.
        \"\"\"
        
        return Prompt(system=system.strip(), user=user.strip())
    
    async def _call_llm(self, prompt: Prompt, options: BaseLLMOptions) -> YourFeatureResult:
        \"\"\"Вызываем LLM и получаем структурированный результат.\"\"\"
        return await self._llm.generate_structured(
            prompt=prompt,
            schema=YourFeatureResult,
            temperature=options.temperature
        )
    
    def _merge_with_defaults(self, options: BaseLLMOptions) -> BaseLLMOptions:
        \"\"\"Мержим пользовательские опции с дефолтами.\"\"\"
        if isinstance(options, YourFeatureOptions):
            return YourFeatureOptions(
                temperature=options.temperature or self._settings.temperature,
                analysis_depth=getattr(options, 'analysis_depth', self._settings.analysis_depth),
                **options.model_dump(exclude_unset=True)
            )
        else:
            # Fallback для BaseLLMOptions
            return YourFeatureOptions(
                temperature=options.temperature or self._settings.temperature,
                analysis_depth=self._settings.analysis_depth,
                language=options.language,
                extra_context=options.extra_context
            )
    
    def get_feature_name(self) -> str:
        return \"your_feature\"
    
    def get_supported_versions(self) -> list[str]:
        return [\"v1\"]
```

### Шаг 6: Создаем bootstrap (`bootstrap.py`)

```python
# src/llm_your_feature/bootstrap.py
from src.llm_features.registry import get_global_registry
from .service import YourFeatureGenerator

def register_your_feature():
    \"\"\"Регистрируем фичу в глобальном реестре.\"\"\"
    registry = get_global_registry()
    
    registry.register(
        name=\"your_feature\",
        generator_class=YourFeatureGenerator,
        version=\"v1\",
        description=\"Описание вашей фичи\",
        set_as_default=True
    )
```

### Шаг 7: Экспорты и автоматическая регистрация (`__init__.py`)

```python
# src/llm_your_feature/__init__.py
from .service import YourFeatureGenerator
from .models import YourFeatureResult
from .options import YourFeatureOptions
from .bootstrap import register_your_feature

# 🚀 АВТОМАТИЧЕСКАЯ РЕГИСТРАЦИЯ при импорте модуля
try:
    register_your_feature()
except Exception:
    # Игнорируем ошибки (например, отсутствие OPENAI_API_KEY)
    pass

__all__ = [
    \"YourFeatureGenerator\",
    \"YourFeatureResult\", 
    \"YourFeatureOptions\",
    \"register_your_feature\",
]
```

### Шаг 8: Добавляем в API (`webapp/app.py`)

```python
# src/webapp/app.py
# Просто добавьте один импорт:
import src.llm_your_feature  # Автоматически регистрирует фичу!

# Всё! Фича уже доступна по POST /features/your_feature/generate
```

### Шаг 9: Настраиваем environment (`.env`)

```bash
# Добавьте в .env файл:
YOUR_FEATURE_TEMPERATURE=0.2
YOUR_FEATURE_ANALYSIS_DEPTH=\"deep\"
YOUR_FEATURE_LANGUAGE=\"ru\"
YOUR_FEATURE_QUALITY_CHECKS=true
```

## 📝 Контракт фичи

Каждая фича **MUST** реализовать:

### 1. Наследование от `AbstractLLMGenerator[T]`
```python
class YourGenerator(AbstractLLMGenerator[YourResultType]):
```

### 2. Обязательные методы:
```python
async def _build_prompt(self, resume, vacancy, options) -> Prompt
async def _call_llm(self, prompt, options) -> YourResultType  
def _merge_with_defaults(self, options) -> BaseLLMOptions
def get_feature_name(self) -> str
def get_supported_versions(self) -> list[str]
```

### 3. Pydantic модель результата:
```python
class YourResult(BaseModel):
    # Ваши поля с типами и описаниями
```

### 4. Регистрация в `bootstrap.py`:
```python
def register_your_feature():
    registry.register(name=\"your_name\", generator_class=YourClass, ...)
```

### 5. Автоматический импорт в `__init__.py`:
```python
try:
    register_your_feature()
except Exception:
    pass
```

## ⚙️ Конфигурация

### Environment переменные

Используйте префикс `{FEATURE_NAME}_` для ваших настроек:

```bash
# Базовые настройки (наследуются от BaseFeatureSettings)
YOUR_FEATURE_LANGUAGE=\"ru\"
YOUR_FEATURE_TEMPERATURE=0.3
YOUR_FEATURE_MODEL_NAME=\"gpt-4o-mini\"
YOUR_FEATURE_PROMPT_VERSION=\"v1\"
YOUR_FEATURE_QUALITY_CHECKS=true

# Ваши кастомные настройки
YOUR_FEATURE_ANALYSIS_DEPTH=\"deep\"
YOUR_FEATURE_MAX_RECOMMENDATIONS=5
```

### Настройки в коде

```python
class YourSettings(BaseFeatureSettings):
    # Наследуете базовые: language, temperature, model_name, etc.
    
    # Добавляете свои
    analysis_depth: str = Field(default=\"surface\")
    
    model_config = ConfigDict(
        env_prefix=\"YOUR_FEATURE_\",  # ← Важно!
        env_file=\".env\"
    )
```

## 🌐 API Integration

После создания фичи она **автоматически** доступна через:

### Список всех фич:
```http
GET /features
```

**Ответ:**
```json
{
  \"features\": [
    {
      \"name\": \"your_feature\",
      \"version\": \"v1\",
      \"generator_class\": \"YourFeatureGenerator\",
      \"description\": \"Описание фичи\"
    }
  ]
}
```

### Генерация:
```http
POST /features/your_feature/generate
Content-Type: application/json

{
  \"resume\": { /* ResumeInfo object */ },
  \"vacancy\": { /* VacancyInfo object */ },
  \"options\": {
    \"temperature\": 0.5,
    \"analysis_depth\": \"deep\"
  },
  \"version\": \"v1\"  // опционально
}
```

**Ответ:**
```json
{
  \"feature_name\": \"your_feature\",
  \"version\": \"v1\",
  \"result\": {
    \"summary\": \"Анализ показал...\",
    \"recommendations\": [\"Изучить Python\", \"Добавить опыт\"],
    \"score\": 0.75
  },
  \"formatted_output\": \"Текстовый вывод (если есть)\"
}
```

## 📚 Примеры

### Смотрите готовые реализации:

#### 1. **Cover Letter** (`src/llm_cover_letter/`)
- **Назначение**: генерация персонализированных сопроводительных писем
- **Модель результата**: `EnhancedCoverLetter` 
- **Особенности**: версионирование промптов (v1, v2), валидация качества, email форматирование
- **API**: `POST /features/cover_letter/generate`

#### 2. **Gap Analyzer** (`src/llm_gap_analyzer/`)
- **Назначение**: детальный GAP-анализ резюме по вакансии с HR методологией
- **Модель результата**: `EnhancedResumeTailoringAnalysis`
- **Особенности**: 6-этапная методология, структурированные рекомендации, расчёт процента соответствия
- **API**: `POST /features/gap_analyzer/generate`

#### Примеры использования:
```bash
# Cover Letter
python -m examples.generate_cover_letter --resume-pdf tests/data/resume.pdf --vacancy tests/data/vacancy.json

# Gap Analyzer  
python -m examples.generate_gap_analysis --resume-pdf tests/data/resume.pdf --vacancy tests/data/vacancy.json

# Показать промпты
python -m examples.show_full_prompt --feature cover_letter
python -m examples.show_full_gap_prompt --prompt-version gap_analyzer.v1
```

### Типичные ошибки и решения:

❌ **Фича не появляется в API**
```python
# Забыли импортировать в webapp/app.py:
import src.llm_your_feature  # ← Добавьте эту строку!
```

❌ **Ошибка создания генератора**
```bash
# Не установлен OPENAI_API_KEY
export OPENAI_API_KEY=\"your-key-here\"
```

❌ **Конфигурация не загружается**
```python
# Неправильный префикс в settings:
model_config = ConfigDict(
    env_prefix=\"YOUR_FEATURE_\",  # ← Должно совпадать с .env
)
```

## 🔧 Troubleshooting

### Проблема: \"Feature not found\"
**Решение:** Проверьте, что модуль импортируется в `webapp/app.py`

### Проблема: \"The api_key client option must be set\"  
**Решение:** Установите `OPENAI_API_KEY` в environment

### Проблема: Настройки не применяются
**Решение:** Проверьте префикс в `env_prefix` и имена переменных в `.env`

### Проблема: Ошибка при импорте
**Решение:** Добавьте `try/except` в `__init__.py` вокруг регистрации

---

## 🎯 Checklist для новой фичи:

- [ ] Создал структуру папок
- [ ] Определил модель результата (`models.py`)
- [ ] Создал опции (`options.py`) 
- [ ] Настроил конфигурацию (`config.py`) с правильным префиксом
- [ ] Реализовал генератор (`service.py`) с 5 обязательными методами
- [ ] Создал bootstrap (`bootstrap.py`) с регистрацией
- [ ] Настроил автоматический импорт (`__init__.py`)
- [ ] Добавил импорт в `webapp/app.py`
- [ ] Добавил переменные в `.env`
- [ ] Проверил через `GET /features` что фича появилась
- [ ] Протестировал через `POST /features/{name}/generate`

**Готово! Ваша фича теперь часть системы! 🎉**

---

*Если что-то не работает — перечитайте README еще раз, 90% проблем решается внимательным следованием инструкции.*