# src/llm_cover_letter/models.py
# --- agent_meta ---
# role: llm-cover-letter-models
# owner: @backend
# contract: Pydantic модели для сопроводительного письма и вспомогательных структур
# last_reviewed: 2025-08-10
# interfaces:
#   - RoleType (Enum)
#   - CompanyContext
#   - SkillsMatchAnalysis
#   - PersonalizationStrategy
#   - EnhancedCoverLetter
# --- /agent_meta ---

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class RoleType(str, Enum):
    """Тип IT-роли для адаптации стиля письма"""

    DEVELOPER = "DEVELOPER"
    QA_ENGINEER = "QA_ENGINEER"
    ANALYST = "ANALYST"
    DEVOPS = "DEVOPS"
    DESIGNER = "DESIGNER"
    MANAGER = "MANAGER"
    ML_ENGINEER = "ML_ENGINEER"
    DATA_SCIENTIST = "DATA_SCIENTIST"
    OTHER = "OTHER"


class CompanyContext(BaseModel):
    """Контекст компании для персонализации"""

    company_name: str = Field(..., description="Название компании")
    company_size: Literal["STARTUP", "MEDIUM", "LARGE", "ENTERPRISE"] = Field(
        ..., description="Размер компании для адаптации тона"
    )
    company_culture: Optional[str] = Field(
        None, description="Особенности культуры компании (если упомянуты в вакансии)"
    )
    product_info: Optional[str] = Field(
        None,
        description="Краткое описание продукта/сервиса или проекта из описания вакансии",
    )

    class Config:
        extra = "forbid"


class SkillsMatchAnalysis(BaseModel):
    """Анализ соответствия навыков требованиям"""

    matched_skills: List[str] = Field(
        ..., min_items=1, description="Навыки кандидата, точно совпадающие с требованиями"
    )
    relevant_experience: str = Field(..., description="Наиболее релевантный опыт для данной позиции")
    quantified_achievement: Optional[str] = Field(
        None, description="Конкретное достижение с цифрами, релевантное вакансии"
    )
    growth_potential: Optional[str] = Field(
        None, description="Чему готов научиться, если есть пробелы в навыках"
    )

    class Config:
        extra = "forbid"


class PersonalizationStrategy(BaseModel):
    """Стратегия персонализации письма"""

    company_hook: str = Field(..., description="Зацепка: что конкретно привлекает в компании/продукте")
    role_motivation: str = Field(..., description="Мотивация именно для этой роли и уровня")
    value_proposition: str = Field(..., description="Конкретная ценность, которую принесет кандидат")

    class Config:
        extra = "forbid"


class EnhancedCoverLetter(BaseModel):
    """
    Профессиональное сопроводительное письмо на основе лучших практик
    """

    # Мета-информация для анализа
    role_type: RoleType = Field(..., description="Тип роли для адаптации стиля")
    company_context: CompanyContext = Field(..., description="Контекст компании")
    estimated_length: Literal["SHORT", "MEDIUM", "LONG"] = Field(
        ...,
        description=(
            "Оценка длины письма в зависимости от уровня кандидата и его вклада"
        ),
    )
    
    # Рекомендации по улучшению
    improvement_suggestions: List[str] = Field(
        ..., description="Конкретные рекомендации по улучшению"
    )

    # Анализ соответствия
    skills_match: SkillsMatchAnalysis = Field(..., description="Анализ соответствия навыков")
    personalization: PersonalizationStrategy = Field(
        ..., description="Стратегия персонализации"
    )

    # Структура письма
    subject_line: str = Field(..., max_length=100, description="Тема письма")
    personalized_greeting: str = Field(..., description="Персонализированное приветствие")
    opening_hook: str = Field(
        ..., max_length=500, description="Зацепляющее начало: краткая история успеха с конкретными цифрами ИЛИ достижение, связанное с продуктом компании. НЕ 'Меня заинтересовала ваша вакансия'"
    )
    company_interest: str = Field(
        ..., max_length=400, description="Конкретное знание о компании/продукте, личная связь с ценностями или подходами. НЕ общие фразы типа 'лидер рынка'"
    )
    relevant_experience: str = Field(
        ..., max_length=400, description="1-2 самых релевантных достижения с конкретными цифрами и точные совпадения навыков из требований вакансии"
    )
    value_demonstration: str = Field(
        ..., max_length=500, description="КАК конкретные навыки решат задачи работодателя. Фокус на ценности для компании с релевантными метриками и достижениями"
    )
    growth_mindset: Optional[str] = Field(
        None, max_length=250, description="Готовность к развитию при пробелах"
    )
    professional_closing: str = Field(
        ..., max_length=300, description="Профессиональное завершение с энтузиазмом и конкретным call-to-action (готовность к интервью)"
    )
    signature: str = Field(..., description="Подпись с контактной информацией")

    # Оценка качества
    personalization_score: int = Field(
        ..., ge=1, le=10, description="Оценка персонализации (1-10)"
    )
    professional_tone_score: int = Field(
        ..., ge=1, le=10, description="Оценка профессиональности тона (1-10)"
    )
    relevance_score: int = Field(
        ..., ge=1, le=10, description="Оценка релевантности содержания (1-10)"
    )

    class Config:
        extra = "forbid"
        title = "EnhancedCoverLetter"
