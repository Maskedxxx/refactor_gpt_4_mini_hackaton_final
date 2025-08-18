# src/llm_interview_checklist/models.py
# --- agent_meta ---
# role: llm-interview-checklist-models
# owner: @backend
# contract: Pydantic модели для результатов генерации профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - ProfessionalInterviewChecklist
#   - PersonalizationContext
#   - PreparationTimeEstimate
#   - TechnicalPreparationItem
#   - BehavioralPreparationItem
#   - CompanyResearchItem
#   - TechnicalStackItem
#   - PracticalExerciseItem
#   - InterviewSetupItem
#   - AdditionalActionItem
# --- /agent_meta ---

from typing import List, Literal
from pydantic import BaseModel, Field
from enum import Enum


class CandidateLevel(str, Enum):
    """Уровень кандидата для адаптации подготовки"""
    JUNIOR = "JUNIOR"           # Начинающий специалист (до 3 лет)
    MIDDLE = "MIDDLE"           # Специалист с опытом (3-6 лет)
    SENIOR = "SENIOR"           # Ведущий специалист (6+ лет)
    LEAD = "LEAD"               # Тимлид/Техлид


class VacancyType(str, Enum):
    """Тип вакансии для адаптации чек-листа"""
    DEVELOPER = "DEVELOPER"                 # Backend/Frontend/Mobile разработчик
    QA_ENGINEER = "QA_ENGINEER"             # Тестировщик
    DATA_SPECIALIST = "DATA_SPECIALIST"     # Data Scientist/Analyst
    BUSINESS_ANALYST = "BUSINESS_ANALYST"   # Бизнес/Системный аналитик
    DESIGNER = "DESIGNER"                   # UI/UX дизайнер
    DEVOPS = "DEVOPS"                       # DevOps/SRE инженер
    MANAGER = "MANAGER"                     # Project Manager/Product Manager
    OTHER = "OTHER"                         # Другие роли


class CompanyFormat(str, Enum):
    """Формат компании для адаптации стиля подготовки"""
    STARTUP = "STARTUP"                     # Стартап
    MEDIUM_COMPANY = "MEDIUM_COMPANY"       # Средняя компания
    LARGE_CORP = "LARGE_CORP"               # Крупная корпорация
    INTERNATIONAL = "INTERNATIONAL"         # Международная компания


class Priority(str, Enum):
    """Приоритет задачи подготовки"""
    CRITICAL = "КРИТИЧНО"       # Без этого точно откажут
    IMPORTANT = "ВАЖНО"         # Сильно влияет на решение
    DESIRED = "ЖЕЛАТЕЛЬНО"      # Плюс, но не критично


# =============================================================================
# Технические модели для каждого блока подготовки
# =============================================================================

class TechnicalPreparationItem(BaseModel):
    """Элемент технической подготовки"""
    category: Literal["профильные_знания", "недостающие_технологии", 
                     "практические_задачи", "проекты_код", "дополнительные_материалы"] = Field(
        ..., description="Категория технической подготовки")
    task_title: str = Field(..., description="Название задачи")
    description: str = Field(..., description="Подробное описание того, что нужно изучить/повторить")
    priority: Priority = Field(..., description="Приоритет выполнения")
    estimated_time: str = Field(..., description="Примерное время на выполнение")
    specific_resources: List[str] = Field(..., description="Конкретные ресурсы (книги, курсы, платформы)")
    success_criteria: str = Field(..., description="Критерии успешного выполнения")


class BehavioralPreparationItem(BaseModel):
    """Элемент поведенческой подготовки"""
    category: Literal["типовые_вопросы", "самопрезентация", "поведенческое_интервью", 
                     "storytelling"] = Field(
        ..., description="Категория поведенческой подготовки")
    task_title: str = Field(..., description="Название задачи подготовки")
    description: str = Field(..., description="Описание того, что нужно подготовить")
    example_questions: List[str] = Field(..., description="Примеры вопросов для подготовки")
    star_method_guidance: str = Field(None, description="Руководство по применению STAR метода")
    practice_tips: str = Field(..., description="Советы по отработке")


class CompanyResearchItem(BaseModel):
    """Элемент изучения компании"""
    category: Literal["исследование_компании", "продукты_отрасль", 
                     "вопросы_работодателю"] = Field(
        ..., description="Категория изучения компании")
    task_title: str = Field(..., description="Что именно изучить")
    specific_actions: List[str] = Field(..., description="Конкретные действия для выполнения")
    priority: Priority = Field(..., description="Приоритет изучения")
    time_required: str = Field(..., description="Необходимое время")


class TechnicalStackItem(BaseModel):
    """Элемент изучения технического стека"""
    category: Literal["требования_вакансии", "технологии_компании", "рабочие_процессы", 
                     "терминология"] = Field(
        ..., description="Категория изучения стека")
    task_title: str = Field(..., description="Название задачи")
    description: str = Field(..., description="Что конкретно изучить")
    relevance_explanation: str = Field(..., description="Почему это важно для данной вакансии")
    study_approach: str = Field(..., description="Как лучше изучить")


class PracticalExerciseItem(BaseModel):
    """Элемент практических упражнений"""
    category: Literal["тренировочные_задачи", "кейсы_опыта", "мок_интервью", 
                     "тестовые_задания", "портфолио"] = Field(
        ..., description="Категория практических упражнений")
    exercise_title: str = Field(..., description="Название упражнения")
    description: str = Field(..., description="Описание упражнения")
    difficulty_level: Literal["базовый", "средний", "продвинутый"] = Field(..., 
                                                                           description="Уровень сложности")
    practice_resources: List[str] = Field(..., description="Ресурсы для практики")
    expected_outcome: str = Field(..., description="Ожидаемый результат")


class InterviewSetupItem(BaseModel):
    """Элемент настройки окружения для интервью"""
    category: Literal["оборудование_связь", "место_проведения", "аккаунты_доступы", 
                     "резервные_варианты", "внешний_вид"] = Field(
        ..., description="Категория настройки окружения")
    task_title: str = Field(..., description="Что нужно подготовить")
    checklist_items: List[str] = Field(..., description="Чек-лист конкретных действий")
    importance_explanation: str = Field(..., description="Почему это важно")


class AdditionalActionItem(BaseModel):
    """Дополнительное действие кандидата"""
    category: Literal["рекомендации", "профили", "документы", "резюме_письмо", 
                     "настрой_отдых"] = Field(
        ..., description="Категория дополнительного действия")
    action_title: str = Field(..., description="Название действия")
    description: str = Field(..., description="Описание действия")
    urgency: Priority = Field(..., description="Срочность выполнения")
    implementation_steps: List[str] = Field(..., description="Шаги выполнения")


# =============================================================================
# Контекстные модели
# =============================================================================

class PersonalizationContext(BaseModel):
    """Контекст персонализации чек-листа"""
    candidate_level: CandidateLevel = Field(..., description="Определенный уровень кандидата")
    vacancy_type: VacancyType = Field(..., description="Тип вакансии")
    company_format: CompanyFormat = Field(..., description="Формат компании")
    key_gaps_identified: List[str] = Field(..., description="Выявленные ключевые пробелы")
    candidate_strengths: List[str] = Field(..., description="Сильные стороны кандидата")
    critical_focus_areas: List[str] = Field(..., description="Критические области фокуса")


class PreparationTimeEstimate(BaseModel):
    """Оценка времени подготовки"""
    total_time_needed: str = Field(..., description="Общее время подготовки")
    critical_tasks_time: str = Field(..., description="Время на критические задачи")
    important_tasks_time: str = Field(..., description="Время на важные задачи")
    optional_tasks_time: str = Field(..., description="Время на желательные задачи")
    daily_schedule_suggestion: str = Field(..., description="Предложение по ежедневному графику")


# =============================================================================
# Основная модель профессионального чек-листа
# =============================================================================

class ProfessionalInterviewChecklist(BaseModel):
    """
    Профессиональный чек-лист подготовки к интервью на основе HR-экспертизы.
    Соответствует лучшим практикам подготовки IT-кандидатов.
    """
    
    # Метаинформация и контекст
    position_title: str = Field(..., description="Название позиции")
    company_name: str = Field(..., description="Название компании")
    personalization_context: PersonalizationContext = Field(..., description="Контекст персонализации")
    
    # Оценка времени и планирование
    time_estimates: PreparationTimeEstimate = Field(..., description="Оценки времени подготовки")
    
    # Основное введение и стратегия
    executive_summary: str = Field(..., description="Краткое резюме подготовки и ключевые фокусные области")
    preparation_strategy: str = Field(..., description="Стратегия подготовки с учетом специфики ситуации")
    
    # 7 основных блоков подготовки согласно гайду
    technical_preparation: List[TechnicalPreparationItem] = Field(..., 
        description="Блок 1: Техническая подготовка (hard skills)")
    
    behavioral_preparation: List[BehavioralPreparationItem] = Field(..., 
        description="Блок 2: Поведенческая подготовка (soft skills)")
    
    company_research: List[CompanyResearchItem] = Field(..., 
        description="Блок 3: Изучение компании и продукта")
    
    technical_stack_study: List[TechnicalStackItem] = Field(..., 
        description="Блок 4: Изучение технического стека и процессов")
    
    practical_exercises: List[PracticalExerciseItem] = Field(..., 
        description="Блок 5: Практические упражнения и кейсы")
    
    interview_setup: List[InterviewSetupItem] = Field(..., 
        description="Блок 6: Настройка окружения для интервью")
    
    additional_actions: List[AdditionalActionItem] = Field(..., 
        description="Блок 7: Дополнительные действия кандидата")
    
    # Финальные рекомендации и предупреждения
    critical_success_factors: List[str] = Field(..., description="Критические факторы успеха")
    common_mistakes_to_avoid: List[str] = Field(..., description="Типичные ошибки, которых следует избегать")
    last_minute_checklist: List[str] = Field(..., description="Чек-лист последней минуты перед интервью")
    motivation_boost: str = Field(..., description="Мотивационное сообщение и настрой на успех")

    class Config:
        extra = "forbid"
        title = "ProfessionalInterviewChecklist"