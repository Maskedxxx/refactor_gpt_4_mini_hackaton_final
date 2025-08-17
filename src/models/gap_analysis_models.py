# src/models/gap_analysis_models.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

# ---------------------------
# Базовые перечисления
# ---------------------------

class CriticalityLevel(str, Enum):
    """Уровень критичности рекомендации. Значения строго фиксированы для response_format."""
    CRITICAL = "CRITICAL"    # Без этого высок риск отказа
    IMPORTANT = "IMPORTANT"  # Сильно влияет на решение
    DESIRED = "DESIRED"      # Неплохой плюс, но не критично

class ComplianceStatus(str, Enum):
    """Статус соответствия требованию. Не использовать эмодзи в значениях."""
    FULL_MATCH = "FULL_MATCH"        # Полное соответствие
    PARTIAL_MATCH = "PARTIAL_MATCH"  # Частичное соответствие/недостаточная глубина
    MISSING = "MISSING"              # Подтверждений нет
    UNCLEAR = "UNCLEAR"              # Недостаточно данных/неоднозначно

class RequirementType(str, Enum):
    """Тип требования: строго как в методологии промпта."""
    MUST_HAVE = "MUST_HAVE"                 # Без этого работа невозможна
    NICE_TO_HAVE = "NICE_TO_HAVE"           # Желательно, можно дорастить
    ADDITIONAL_BONUS = "ADDITIONAL_BONUS"   # Конкурентное преимущество

class SkillCategory(str, Enum):
    """Категория навыков/аспекта опыта для требования."""
    HARD_SKILLS = "HARD_SKILLS"
    SOFT_SKILLS = "SOFT_SKILLS"
    EXPERIENCE = "EXPERIENCE"
    EDUCATION = "EDUCATION"

class SectionName(str, Enum):
    """Раздел резюме, к которому относится рекомендация (расширенный перечень)."""
    TITLE = "title"                 # Заголовок/позиция/воронка
    SKILLS = "skills"               # Навыки
    EXPERIENCE = "experience"       # Опыт
    EDUCATION = "education"         # Образование
    STRUCTURE = "structure"         # Структура/оформление/читаемость
    PROJECTS = "projects"           # Проекты/кейсы
    ACHIEVEMENTS = "achievements"   # Достижения/метрики/вклад
    CERTIFICATES = "certificates"   # Сертификаты/курсы
    PORTFOLIO = "portfolio"         # Портфолио/GitHub/ссылки
    CONTACTS = "contacts"           # Контакты/линки
    COVER_LETTER = "cover_letter"   # Сопроводительное письмо

class DecisionImpact(str, Enum):
    """Нормализованная сила влияния конкретного требования на решение по кандидату."""
    BLOCKER = "BLOCKER"  # Блокирующий фактор
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

# ---------------------------
# Основные модели
# ---------------------------

class RequirementAnalysis(BaseModel):
    """Анализ одного требования вакансии."""
    requirement_text: str = Field(..., description="Точный текст требования из вакансии")
    requirement_type: RequirementType = Field(..., description="Классификация: MUST_HAVE / NICE_TO_HAVE / ADDITIONAL_BONUS")
    skill_category: SkillCategory = Field(..., description="Категория требования: HARD_SKILLS / SOFT_SKILLS / EXPERIENCE / EDUCATION")

    compliance_status: ComplianceStatus = Field(..., description="Итог соответствия: FULL_MATCH / PARTIAL_MATCH / MISSING / UNCLEAR")
    evidence_in_resume: Optional[str] = Field(
        None,
        description="Краткая цитата или указание раздела/проекта в резюме, подтверждающее соответствие; не выдумывать"
    )
    gap_description: Optional[str] = Field(
        None,
        description="Если соответствие не полное: чего не хватает (глубина, масштаб, срок, версия, домен и т.д.)"
    )

    decision_impact: DecisionImpact = Field(
        ...,
        description="Нормализованная сила влияния данного требования на решение (BLOCKER/HIGH/MEDIUM/LOW)"
    )
    decision_rationale: str = Field(
        ...,
        description="Краткое деловое обоснование влияния (почему это важно именно для данной вакансии)"
    )

class PrimaryScreeningResult(BaseModel):
    """Результат первичного скрининга (7–15 секунд)."""
    job_title_match: bool = Field(
        ...,
        description="Соответствие/близость должности в резюме и вакансии"
    )
    experience_years_match: bool = Field(
        ...,
        description="Суммарный релевантный стаж кандидата не ниже минимального по вакансии"
    )
    key_skills_visible: bool = Field(
        ...,
        description="Ключевые технологии из MUST-требований явно присутствуют в резюме"
    )
    location_suitable: bool = Field(
        ...,
        description="Локация/релокация/удалёнка совместимы с условиями вакансии; при отсутствии данных используйте false и поясните в screening_notes"
    )
    salary_expectations_match: bool = Field(
        ...,
        description="Ожидания кандидата попадают в бюджет вакансии (валюта/брутто/нетто); при отсутствии данных используйте false и поясните в screening_notes"
    )

    overall_screening_result: Literal["ПРИНЯТЬ", "ВОЗМОЖНО", "ОТКЛОНИТЬ"] = Field(
        ...,
        description="Итог скрининга по совокупности сигналов"
    )
    screening_notes: str = Field(
        ...,
        description="Краткие пояснения: где не хватает информации/что требует уточнения"
    )

class DetailedRecommendation(BaseModel):
    """Детальная рекомендация по улучшению резюме (actionable)."""
    section: SectionName = Field(..., description="К какому разделу резюме относится рекомендация")
    criticality: CriticalityLevel = Field(
        ...,
        description="CRITICAL → попадёт в critical_recommendations; IMPORTANT → important_recommendations; DESIRED → optional_recommendations"
    )
    issue_description: str = Field(..., description="Что именно не так сейчас")
    specific_actions: List[str] = Field(..., min_items=1, description="Чёткие действия: добавить/исправить/убрать (список)")
    example_wording: Optional[str] = Field(None, description="Пример удачной формулировки (если применимо)")
    business_rationale: str = Field(..., description="Почему это важно для данной вакансии/бизнес-контекста")

class ResumeQualityAssessment(BaseModel):
    """Качество презентации резюме (шкалы 1–10 с якорями в методологии)."""
    structure_clarity: int = Field(..., ge=1, le=10, description="Структурированность/читабельность (1–10)")
    content_relevance: int = Field(..., ge=1, le=10, description="Релевантность описанного опыта (1–10)")
    achievement_focus: int = Field(..., ge=1, le=10, description="Фокус на достижениях/метриках (1–10)")
    adaptation_quality: int = Field(..., ge=1, le=10, description="Степень адаптации под вакансию (1–10)")

    overall_impression: Literal["СИЛЬНЫЙ", "СРЕДНИЙ", "СЛАБЫЙ"] = Field(..., description="Общее впечатление от резюме")
    quality_notes: str = Field(..., description="Ключевые наблюдения по качеству подачи")

class EnhancedResumeTailoringAnalysis(BaseModel):
    """Главная модель результата GAP-анализа (строго соответствует response_format)."""

    # ЭТАП 1
    primary_screening: PrimaryScreeningResult = Field(..., description="Первичный скрининг (7–15 секунд)")

    # ЭТАПЫ 2–3
    requirements_analysis: List[RequirementAnalysis] = Field(
        ...,
        description="Список нормализованных требований вакансии с оценкой соответствия и влияния"
    )

    # ЭТАП 4
    quality_assessment: ResumeQualityAssessment = Field(..., description="Оценка качества резюме")

    # Рекомендации (группировка по критичности)
    critical_recommendations: List[DetailedRecommendation] = Field(
        ...,
        description="Рекомендации уровня CRITICAL (must-fix)"
    )
    important_recommendations: List[DetailedRecommendation] = Field(
        ...,
        description="Рекомендации уровня IMPORTANT (существенно улучшат)"
    )
    optional_recommendations: List[DetailedRecommendation] = Field(
        ...,
        description="Рекомендации уровня DESIRED (nice-to-have)"
    )

    # Итоги
    overall_match_percentage: int = Field(..., ge=0, le=100, description="Расчётный процент соответствия вакансии (0–100)")
    hiring_recommendation: Literal["СИЛЬНО_ДА", "ДА", "ВОЗМОЖНО", "НЕТ", "СИЛЬНО_НЕТ"] = Field(
        ...,
        description="Рекомендация по найму с учётом политики отбора"
    )
    key_strengths: List[str] = Field(..., min_items=1, description="Ключевые сильные стороны кандидата")
    major_gaps: List[str] = Field(..., description="Основные пробелы/риски, требующие внимания")

    next_steps: List[str] = Field(
        ...,
        description="Список конкретных следующих шагов (вопросы к кандидату/рекрутеру, проверки, артефакты)"
    )

    class Config:
        extra = "forbid"
        title = "EnhancedResumeTailoringAnalysis"
