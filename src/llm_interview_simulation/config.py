# src/llm_interview_simulation/config.py
# --- agent_meta ---
# role: interview-simulation-config
# owner: @backend
# contract: Конфигурация и настройки для модуля симуляции интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewSimulationSettings (настройки по умолчанию)
# --- /agent_meta ---

from __future__ import annotations

import os
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from .models import CompetencyArea, QuestionType, CandidateLevel, ITRole
from .options import InterviewSimulationOptions


class InterviewSimulationSettings(BaseModel):
    """Настройки по умолчанию для симуляции интервью.
    
    Содержит все дефолтные значения, маппинги и конфигурации,
    которые используются для проведения интервью.
    """
    
    # === Базовые настройки ===
    
    feature_name: str = Field(
        default="interview_simulation",
        description="Название фичи в реестре"
    )
    
    feature_version: str = Field(
        default="v1.0",
        description="Версия фичи"
    )
    
    feature_description: str = Field(
        default="Профессиональная симуляция технического интервью с AI",
        description="Описание фичи"
    )
    
    # === OpenAI настройки ===
    
    openai_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="API ключ OpenAI"
    )
    
    openai_model_name: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini-2024-07-18"),
        description="Модель OpenAI для генерации"
    )
    
    # === Дефолтные опции ===
    
    default_options: InterviewSimulationOptions = Field(
        default_factory=lambda: InterviewSimulationOptions(
            prompt_version="v1.0",
            target_rounds=5,
            difficulty_level="medium",
            include_behavioral=True,
            include_technical=True,
            enable_assessment=True,
            hr_personality="neutral",
            candidate_confidence="medium",
            temperature_hr=0.7,
            temperature_candidate=0.8,
            quality_checks=True
        ),
        description="Опции по умолчанию"
    )
    
    # === Маппинги раундов на типы вопросов ===
    
    round_question_mapping: Dict[int, List[QuestionType]] = Field(
        default_factory=lambda: {
            1: [QuestionType.INTRODUCTION],
            2: [QuestionType.TECHNICAL_SKILLS, QuestionType.EXPERIENCE_DEEP_DIVE],
            3: [QuestionType.BEHAVIORAL_STAR, QuestionType.PROBLEM_SOLVING],
            4: [QuestionType.MOTIVATION, QuestionType.CULTURE_FIT],
            5: [QuestionType.FINAL],
            6: [QuestionType.LEADERSHIP],  # Для senior/lead
            7: [QuestionType.FINAL]        # Расширенное интервью
        },
        description="Маппинг раундов на типы вопросов"
    )
    
    # === Маппинги уровней на количество раундов ===
    
    level_rounds_mapping: Dict[CandidateLevel, int] = Field(
        default_factory=lambda: {
            CandidateLevel.JUNIOR: 4,
            CandidateLevel.MIDDLE: 5,
            CandidateLevel.SENIOR: 6,
            CandidateLevel.LEAD: 7,
            CandidateLevel.UNKNOWN: 5
        },
        description="Количество раундов по уровню кандидата"
    )
    
    # === Ключевые слова для определения IT-ролей ===
    
    role_keywords: Dict[ITRole, List[str]] = Field(
        default_factory=lambda: {
            ITRole.DEVELOPER: [
                'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js', 
                'django', 'flask', 'spring', 'разработчик', 'программист', 'developer', 
                'backend', 'frontend', 'fullstack', 'software engineer', 'web developer'
            ],
            ITRole.DATA_SCIENTIST: [
                'data scientist', 'машинное обучение', 'machine learning', 'ml', 'ai', 
                'нейронные сети', 'pytorch', 'tensorflow', 'pandas', 'numpy', 
                'scikit-learn', 'llm', 'nlp', 'computer vision', 'дата-сайентист'
            ],
            ITRole.QA: [
                'тестировщик', 'qa', 'quality assurance', 'тестирование', 'автотесты',
                'selenium', 'cypress', 'junit', 'testing', 'test automation'
            ],
            ITRole.DEVOPS: [
                'devops', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
                'ansible', 'jenkins', 'gitlab', 'ci/cd', 'мониторинг', 'инфраструктура'
            ],
            ITRole.ANALYST: [
                'аналитик', 'analyst', 'бизнес-аналитик', 'системный аналитик',
                'product analyst', 'data analyst', 'bi', 'tableau', 'power bi', 'sql'
            ],
            ITRole.PROJECT_MANAGER: [
                'менеджер проектов', 'project manager', 'scrum master', 'product manager',
                'руководитель проектов', 'agile', 'scrum', 'kanban'
            ],
            ITRole.DESIGNER: [
                'дизайнер', 'designer', 'ui/ux', 'web design', 'graphic design',
                'figma', 'sketch', 'adobe', 'веб-дизайн', 'интерфейс'
            ]
        },
        description="Ключевые слова для автоопределения IT-роли"
    )
    
    # === Технологии по категориям ===
    
    tech_categories: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            'languages': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby'],
            'frameworks': ['django', 'flask', 'fastapi', 'react', 'angular', 'vue', 'spring', 'laravel'],
            'databases': ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sql'],
            'ml_ai': ['pytorch', 'tensorflow', 'scikit-learn', 'pandas', 'numpy', 'langchain', 'llm', 'nlp'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'terraform', 'jenkins', 'gitlab'],
            'tools': ['git', 'jira', 'confluence', 'postman', 'swagger']
        },
        description="Технологии по категориям для анализа резюме"
    )
    
    # === Компетенции по уровням ===
    
    level_competencies: Dict[CandidateLevel, List[CompetencyArea]] = Field(
        default_factory=lambda: {
            CandidateLevel.JUNIOR: [
                CompetencyArea.TECHNICAL_EXPERTISE,
                CompetencyArea.COMMUNICATION,
                CompetencyArea.LEARNING_ABILITY,
                CompetencyArea.MOTIVATION
            ],
            CandidateLevel.MIDDLE: [
                CompetencyArea.TECHNICAL_EXPERTISE,
                CompetencyArea.COMMUNICATION,
                CompetencyArea.PROBLEM_SOLVING,
                CompetencyArea.TEAMWORK,
                CompetencyArea.ADAPTABILITY,
                CompetencyArea.MOTIVATION
            ],
            CandidateLevel.SENIOR: [
                CompetencyArea.TECHNICAL_EXPERTISE,
                CompetencyArea.PROBLEM_SOLVING,
                CompetencyArea.COMMUNICATION,
                CompetencyArea.TEAMWORK,
                CompetencyArea.LEADERSHIP,
                CompetencyArea.ADAPTABILITY,
                CompetencyArea.CULTURAL_FIT
            ],
            CandidateLevel.LEAD: [
                CompetencyArea.TECHNICAL_EXPERTISE,
                CompetencyArea.LEADERSHIP,
                CompetencyArea.PROBLEM_SOLVING,
                CompetencyArea.COMMUNICATION,
                CompetencyArea.TEAMWORK,
                CompetencyArea.CULTURAL_FIT,
                CompetencyArea.ADAPTABILITY
            ]
        },
        description="Основные компетенции для оценки по уровням"
    )
    
    # === Настройки Assessment Engine ===
    
    assessment_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "min_evidence_items": 2,  # Минимум доказательств для оценки
            "red_flag_threshold": 3,  # Максимум красных флагов для conditional_hire
            "cultural_fit_weight": 0.2,  # Вес культурного соответствия
            "technical_expertise_weight": 0.3,  # Вес технической экспертизы
            "hire_threshold": 3.5,  # Минимальный средний балл для hire
            "conditional_hire_threshold": 2.5,  # Минимальный балл для conditional_hire
            "enable_detailed_feedback": True,  # Генерировать детальную обратную связь
            "max_improvement_recommendations": 5  # Максимум рекомендаций по улучшению
        },
        description="Настройки системы оценки"
    )
    
    # === Промпт настройки ===
    
    prompt_settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_context_length": 80000,  # Максимальная длина контекста
            "resume_summary_length": 3500,  # Длина сводки резюме
            "vacancy_summary_length": 3000,  # Длина сводки вакансии
            "dialog_history_limit": 20,  # Максимум сообщений в истории
            "include_examples": True,  # Включать примеры в промпты
            "use_russian_language": True  # Использовать русский язык
        },
        description="Настройки генерации промптов"
    )
    
    class Config:
        """Конфигурация Pydantic модели."""
        extra = "forbid"
        title = "InterviewSimulationSettings"


# Создаем экземпляр настроек по умолчанию
default_settings = InterviewSimulationSettings()


def get_default_options() -> InterviewSimulationOptions:
    """Получить опции по умолчанию для симуляции интервью.
    
    Returns:
        InterviewSimulationOptions: Настройки по умолчанию
    """
    return default_settings.default_options.copy(deep=True)


def get_competencies_for_level(level: CandidateLevel) -> List[CompetencyArea]:
    """Получить список компетенций для оценки по уровню кандидата.
    
    Args:
        level: Уровень кандидата
        
    Returns:
        List[CompetencyArea]: Список компетенций для оценки
    """
    return default_settings.level_competencies.get(
        level, 
        default_settings.level_competencies[CandidateLevel.MIDDLE]
    )


def get_target_rounds_for_level(level: CandidateLevel) -> int:
    """Получить рекомендуемое количество раундов для уровня кандидата.
    
    Args:
        level: Уровень кандидата
        
    Returns:
        int: Количество раундов интервью
    """
    return default_settings.level_rounds_mapping.get(level, 5)


def get_question_types_for_round(round_number: int) -> List[QuestionType]:
    """Получить возможные типы вопросов для раунда.
    
    Args:
        round_number: Номер раунда (1-7)
        
    Returns:
        List[QuestionType]: Список типов вопросов
    """
    return default_settings.round_question_mapping.get(
        round_number, 
        [QuestionType.FINAL]
    )