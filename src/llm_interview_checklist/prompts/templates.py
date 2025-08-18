# src/llm_interview_checklist/prompts/templates.py
# --- agent_meta ---
# role: llm-interview-checklist-prompt-templates
# owner: @backend
# contract: Версионированные шаблоны промптов для генерации профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - INTERVIEW_CHECKLIST_V1_TEMPLATE
#   - create_professional_interview_checklist_prompt()
# --- /agent_meta ---

from typing import Dict, Any

from src.parsing.llm.prompt import PromptTemplate
from ..models import CandidateLevel, VacancyType, CompanyFormat
from .mappings import (
    get_candidate_level_guidance,
    get_vacancy_type_adaptation,
    get_company_format_adaptation,
)


def _build_candidate_level_block(level: CandidateLevel) -> str:
    """Создает блок адаптации под уровень кандидата."""
    guidance = get_candidate_level_guidance(level)
    return f"""
### АДАПТАЦИЯ ПОД УРОВЕНЬ КАНДИДАТА: {level.value}

**Фокус подготовки:** {guidance['focus']}
**Техническая глубина:** {guidance['technical_depth']}
**Поведенческие аспекты:** {guidance['behavioral_focus']}
**Стиль подготовки:** {guidance['preparation_style']}
**Советы для интервью:** {guidance['interview_tips']}
"""


def _build_vacancy_type_block(vacancy_type: VacancyType) -> str:
    """Создает блок адаптации под тип вакансии."""
    adaptation = get_vacancy_type_adaptation(vacancy_type)
    return f"""
### АДАПТАЦИЯ ПОД ТИП РОЛИ: {vacancy_type.value}

**Ключевые области:** {adaptation['key_areas']}
**Технический фокус:** {adaptation['technical_focus']}
**Поведенческие аспекты:** {adaptation['behavioral_aspects']}
**Типичные вопросы:** {adaptation['typical_questions']}
**Ресурсы подготовки:** {adaptation['preparation_resources']}
"""


def _build_company_format_block(company_format: CompanyFormat) -> str:
    """Создает блок адаптации под формат компании."""
    adaptation = get_company_format_adaptation(company_format)
    return f"""
### АДАПТАЦИЯ ПОД ФОРМАТ КОМПАНИИ: {company_format.value}

**Культурный фокус:** {adaptation['culture_focus']}
**Стиль интервью:** {adaptation['interview_style']}
**Ключевые качества:** {adaptation['key_qualities']}
**Советы подготовки:** {adaptation['preparation_tips']}
**Рабочая среда:** {adaptation['typical_environment']}
"""


def _build_extra_context_block(extra_context: Dict[str, Any]) -> str:
    """Создает блок дополнительного контекста, если предоставлен."""
    if not extra_context:
        return ""
    
    context_text = "\n### ДОПОЛНИТЕЛЬНЫЙ КОНТЕКСТ\n\n"
    for key, value in extra_context.items():
        context_text += f"**{key}:** {value}\n"
    context_text += "\n"
    return context_text


# Основной шаблон промпта для профессионального чек-листа
INTERVIEW_CHECKLIST_V1_TEMPLATE = """## ИСХОДНЫЕ ДАННЫЕ ДЛЯ АНАЛИЗА

### ПРОФИЛЬ КАНДИДАТА:
<resume_start>
{formatted_resume}
</resume_end>

### ЦЕЛЕВАЯ ВАКАНСИЯ:
<vacancy_start>
{formatted_vacancy}
</vacancy_end>

{candidate_level_block}

{vacancy_type_block}

{company_format_block}

{extra_context_block}

## МЕТОДОЛОГИЯ СОЗДАНИЯ ПРОФЕССИОНАЛЬНОГО ЧЕК-ЛИСТА

### ЭТАП 1: ПЕРСОНАЛИЗАЦИЯ И СООТВЕТСТВИЕ
Создай чек-лист ИНДИВИДУАЛЬНО под этого кандидата и конкретную позицию:

1. **Анализ GAP'ов**: выдели требуемые навыки vs имеющиеся у кандидата
2. **Учет уровня**: адаптируй сложность под уровень кандидата
3. **Фокус на пробелах**: приоритизируй areas where candidate needs improvement
4. **Leveraging strengths**: используй сильные стороны кандидата как преимущества

### ЭТАП 2: АДАПТАЦИЯ ПОД КОНТЕКСТ
Адаптируй подготовку под специфику роли и компании согласно блокам адаптации выше.

## 7 ОБЯЗАТЕЛЬНЫХ БЛОКОВ ПРОФЕССИОНАЛЬНОГО ЧЕК-ЛИСТА

### БЛОК 1: ТЕХНИЧЕСКАЯ ПОДГОТОВКА
Включи 5 категорий:

**1.1 Профильные знания** (повторение core knowledge)
- Определи ключевые темы без которых не обойтись на данной позиции
- Адаптируй под уровень: junior - основы, senior - углубленные вопросы
- Укажи конкретные источники для повторения

**1.2 Недостающие технологии** (gap filling)
- Выяви технологии из вакансии, которых мало/нет в резюме
- Составь план изучения основ (не стать экспертом, а понимать о чем речь)

**1.3 Практические задачи** (hands-on preparation)
- Подбери типичные задачи для данной роли и уровня
- Конкретные платформы: LeetCode, HackerRank, Codewars и др.
- Примеры задач с разбором решений

**1.4 Проекты и код кандидата** (portfolio preparation)
- Анализ имеющихся проектов в резюме
- Подготовка к обсуждению: технические решения, архитектура, challenges

**1.5 Дополнительные материалы** (advanced topics)
- Специфичные для роли: паттерны, методологии, best practices
- Актуальные тренды в области

### БЛОК 2: ПОВЕДЕНЧЕСКАЯ ПОДГОТОВКА (SOFT SKILLS)
Включи 4 категории:

**2.1 Типовые вопросы о кандидате**
- "Расскажите о себе", сильные/слабые стороны, motivation
- Подготовка STAR-историй для демонстрации качеств
- Примеры вопросов и структура ответов

**2.2 Тренировка самопрезентации**
- 2-3 минутный pitch about experience
- Презентация ключевого проекта
- Практика: проговорить вслух, записать на видео

**2.3 Поведенческое интервью**
- Работа в команде, конфликты, leadership, неудачи, стресс
- STAR method examples для каждой компетенции
- Адаптация под культуру компании

**2.4 Storytelling и позитивный настрой**
- Фокус на достижения и вклад
- Избегание негатива про предыдущих работодателей
- Демонстрация growth mindset

### БЛОК 3: ИЗУЧЕНИЕ КОМПАНИИ И ПРОДУКТА
Включи 3 категории:

**3.1 Исследование компании**
- Сайт, новости, пресс-релизы, ценности, миссия
- LinkedIn профили команды и интервьюеров
- История и достижения компании

**3.2 Продукты и отрасль**
- Изучение флагманского продукта, установка demo
- Понимание бизнес-модели и target audience
- Анализ конкурентов и позиционирования

**3.3 Вопросы для работодателя**
- 3-5 умных вопросов показывающих интерес и экспертизу
- Избегание вопросов с очевидными ответами с сайта
- Фокус на будущем развитии и возможностях

### БЛОК 4: ИЗУЧЕНИЕ ТЕХНИЧЕСКОГО СТЕКА И ПРОЦЕССОВ
Включи 4 категории:

**4.1 Разбор требований вакансии**
- Детальный анализ JD, выписать все технологии
- Сопоставление с experience кандидата
- Приоритизация областей для изучения

**4.2 Технологии компании**
- Используемый stack (из вакансии, открытых источников)
- Изучение основ незнакомых технологий
- Подготовка к вопросам про architectural choices

**4.3 Рабочие процессы и методологии**
- Code review, CI/CD, testing practices
- Agile/Scrum/Kanban processes
- Development lifecycle в компании

**4.4 Терминология и жаргон**
- Специфичные термины из вакансии
- Industry-specific vocabulary
- Понимание acronyms и technical concepts

### БЛОК 5: ПРАКТИЧЕСКИЕ УПРАЖНЕНИЯ И КЕЙСЫ
Включи 5 категорий:

**5.1 Тренировочные задачи**
- Конкретные задачи под уровень и специализацию
- Платформы и ресурсы для практики
- Daily practice routine до интервью

**5.2 Кейсы из опыта**
- 2-3 prepared stories демонстрирующих разные skills
- STAR format для структурирования
- Practice delivery: четкость, краткость, impact

**5.3 Мок-интервью**
- Симуляция с коллегой или другом
- Запись на камеру для self-review
- Feedback и iteration on answers

**5.4 Тестовые задания**
- Если известно о home assignment - подготовка environment
- Review типичных тестовых заданий для роли
- Time management и presentation подготовка

**5.5 Портфолио и демо-материалы**
- Ревизия проектов в GitHub/портфолио
- Подготовка live demo (если применимо)
- README и documentation update

### БЛОК 6: НАСТРОЙКА ОКРУЖЕНИЯ ДЛЯ ИНТЕРВЬЮ
Включи 5 категорий:

**6.1 Оборудование и связь**
- Тестирование камеры, микрофона, интернета
- Backup план при technical issues
- Platform setup (Zoom, Teams, etc.)

**6.2 Место проведения**
- Quiet, professional environment
- Lighting и background setup
- Notifications отключение

**6.3 Аккаунты и доступы**
- Platform registration и testing
- Contact information для emergency
- Link testing и preparation

**6.4 Резервные варианты**
- Backup internet connection (mobile hotspot)
- Alternative contact methods
- Plan B при force majeure

**6.5 Внешний вид и окружение**
- Professional attire appropriate для company culture
- Clean, organized space in camera view
- Professional демeanor preparation

### БЛОК 7: ДОПОЛНИТЕЛЬНЫЕ ДЕЙСТВИЯ КАНДИДАТА
Включи 5 категорий:

**7.1 Рекомендации**
- Подготовка списка references
- Получение согласия на рекомендации
- Briefing рекомендателей о позиции

**7.2 Профили и онлайн-присутствие**
- LinkedIn, GitHub, portfolio consistency check
- Removal/hiding неподходящего content
- Professional online image curation

**7.3 Документы и сертификаты**
- Copies сертификатов и дипломов
- Updated resume final version
- Portfolio/work samples preparation

**7.4 Резюме и сопроводительное письмо**
- Final resume review и customization
- Cover letter адаптация (если требуется)
- Consistency across materials

**7.5 Настрой и отдых**
- Mental preparation и confidence building
- Rest и proper nutrition before interview
- Stress management techniques

## КРИТЕРИИ КАЧЕСТВЕННОГО ЧЕК-ЛИСТА

✅ **Персонализация**: каждый пункт adapted под кандидата и вакансию
✅ **Конкретность**: четкие действия, ресурсы, временные рамки
✅ **Приоритизация**: критично/важно/желательно
✅ **Реалистичность**: выполнимо в имеющееся время
✅ **Полнота**: покрывает все аспекты подготовки
✅ **Actionable**: clear next steps для кандидата

## ИНСТРУКЦИИ ПО РЕЗУЛЬТАТУ

1. **Анализируй контекст**: учитывай специфику кандидата, вакансии, компании
2. **Персонализируй полностью**: никаких generic советов
3. **Детализируй конкретно**: что, где, как, сколько времени
4. **Приоритизируй разумно**: от critical к nice-to-have
5. **Структурируй четко**: соблюдай все 7 блоков
6. **Мотивируй кандидата**: positive tone, confidence building

Создай professional interview checklist в формате JSON согласно модели ProfessionalInterviewChecklist.
Пиши на русском языке. Будь максимально конкретным и практичным.
"""


def create_professional_interview_checklist_prompt(
    formatted_resume: str,
    formatted_vacancy: str,
    candidate_level: CandidateLevel,
    vacancy_type: VacancyType,
    company_format: CompanyFormat,
    extra_context: Dict[str, Any] = None,
) -> PromptTemplate:
    """
    Создает полный промпт для генерации профессионального чек-листа подготовки к интервью.
    
    Args:
        formatted_resume: Отформатированное резюме
        formatted_vacancy: Отформатированная вакансия
        candidate_level: Уровень кандидата
        vacancy_type: Тип вакансии
        company_format: Формат компании
        extra_context: Дополнительный контекст
        
    Returns:
        Готовый промпт для LLM
    """
    # Сборка динамических блоков
    candidate_level_block = _build_candidate_level_block(candidate_level)
    vacancy_type_block = _build_vacancy_type_block(vacancy_type)
    company_format_block = _build_company_format_block(company_format)
    extra_context_block = _build_extra_context_block(extra_context or {})
    
    # System prompt - роль и методология
    system_prompt = """Ты — ведущий HR-эксперт с 10+ летним опытом подготовки IT-кандидатов к интервью.

## ЭКСПЕРТНАЯ КВАЛИФИКАЦИЯ
- Специализация: составление персонализированных чек-листов подготовки к IT-интервью
- Опыт: успешная подготовка 1000+ кандидатов разных уровней
- Методология: следуешь лучшим практикам HR-индустрии и современным трендам
- Подход: индивидуальная адаптация под каждого кандидата и вакансию

Твоя задача: создать профессиональный чек-лист подготовки к интервью в формате ProfessionalInterviewChecklist."""
    
    # User prompt - данные и инструкции
    user_prompt = INTERVIEW_CHECKLIST_V1_TEMPLATE.format(
        formatted_resume=formatted_resume,
        formatted_vacancy=formatted_vacancy,
        candidate_level_block=candidate_level_block,
        vacancy_type_block=vacancy_type_block,
        company_format_block=company_format_block,
        extra_context_block=extra_context_block,
    )
    
    return PromptTemplate(
        name="interview_checklist",
        version="v1", 
        system_tmpl=system_prompt,
        user_tmpl=user_prompt
    )