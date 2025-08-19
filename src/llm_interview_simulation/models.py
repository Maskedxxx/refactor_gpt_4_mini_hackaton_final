# src/llm_interview_simulation/models.py
# --- agent_meta ---
# role: interview-simulation-models
# owner: @backend
# contract: Модели данных для симуляции интервью, адаптированные для LLM Features Framework
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewSimulation (основной результат генерации)
#   - DialogMessage (сообщение в диалоге)
#   - CandidateProfile (профиль кандидата)
#   - InterviewAssessment (детальная оценка)
# --- /agent_meta ---

from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class CandidateLevel(str, Enum):
    """Уровень кандидата определенный автоматически из резюме."""
    JUNIOR = "junior"
    MIDDLE = "middle" 
    SENIOR = "senior"
    LEAD = "lead"
    UNKNOWN = "unknown"


class ITRole(str, Enum):
    """Тип IT-роли определенный автоматически из резюме."""
    DEVELOPER = "developer"
    QA = "qa"
    DEVOPS = "devops"
    ANALYST = "analyst"
    PROJECT_MANAGER = "project_manager"
    DESIGNER = "designer"
    DATA_SCIENTIST = "data_scientist"
    SYSTEM_ADMIN = "system_admin"
    OTHER = "other"


class QuestionType(str, Enum):
    """Типы вопросов в структурированном интервью."""
    INTRODUCTION = "introduction"           # Знакомство и общие вопросы
    TECHNICAL_SKILLS = "technical_skills"   # Проверка технических навыков
    EXPERIENCE_DEEP_DIVE = "experience"     # Глубокое обсуждение опыта
    BEHAVIORAL_STAR = "behavioral"          # Поведенческие вопросы (STAR методика)
    PROBLEM_SOLVING = "problem_solving"     # Решение проблем и кейсы
    MOTIVATION = "motivation"               # Мотивация и цели
    CULTURE_FIT = "culture_fit"            # Соответствие культуре
    LEADERSHIP = "leadership"               # Лидерские качества
    FINAL = "final"                        # Финальные вопросы


class CompetencyArea(str, Enum):
    """Области компетенций для профессиональной оценки."""
    TECHNICAL_EXPERTISE = "technical_expertise"     # Техническая экспертиза
    PROBLEM_SOLVING = "problem_solving"              # Решение проблем
    COMMUNICATION = "communication"                  # Коммуникативные навыки
    TEAMWORK = "teamwork"                           # Работа в команде
    ADAPTABILITY = "adaptability"                   # Адаптивность
    LEADERSHIP = "leadership"                       # Лидерские качества
    LEARNING_ABILITY = "learning_ability"           # Способность к обучению
    MOTIVATION = "motivation"                       # Мотивация
    CULTURAL_FIT = "cultural_fit"                   # Культурное соответствие


class DialogMessage(BaseModel):
    """Сообщение в диалоге между HR и кандидатом.
    
    Содержит полную информацию о каждом обмене репликами в интервью,
    включая метаданные для анализа качества диалога.
    """
    speaker: Literal["HR", "Candidate"] = Field(
        ..., 
        description="Кто говорит: HR-менеджер или кандидат"
    )
    message: str = Field(
        ..., 
        description="Текст сообщения (вопрос или ответ)"
    )
    round_number: int = Field(
        ..., 
        description="Номер раунда диалога (1, 2, 3...)"
    )
    question_type: Optional[QuestionType] = Field(
        None, 
        description="Тип вопроса (только для HR-сообщений)"
    )
    response_quality: Optional[int] = Field(
        None, 
        ge=1, 
        le=5, 
        description="Оценка качества ответа 1-5 (только для кандидата)"
    )
    key_points: List[str] = Field(
        default_factory=list, 
        description="Ключевые моменты из ответа для анализа"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Временная метка создания сообщения"
    )


class CompetencyScore(BaseModel):
    """Оценка по конкретной компетенции с доказательствами.
    
    Детальная оценка одной области компетенций на основе ответов кандидата.
    """
    area: CompetencyArea = Field(
        ..., 
        description="Область компетенции для оценки"
    )
    score: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="Оценка от 1 (неудовлетворительно) до 5 (превосходно)"
    )
    evidence: List[str] = Field(
        default_factory=list, 
        description="Конкретные доказательства/цитаты из ответов кандидата"
    )
    improvement_notes: str = Field(
        "", 
        description="Рекомендации по улучшению данной компетенции"
    )


class InterviewAssessment(BaseModel):
    """Детальная профессиональная оценка результатов интервью.
    
    Всесторонняя оценка кандидата включающая анализ компетенций,
    выявление сильных/слабых сторон и итоговые рекомендации.
    """
    overall_recommendation: Literal["hire", "conditional_hire", "reject"] = Field(
        ..., 
        description="Общая рекомендация по найму"
    )
    competency_scores: List[CompetencyScore] = Field(
        ..., 
        description="Детальные оценки по каждой компетенции"
    )
    strengths: List[str] = Field(
        ..., 
        description="Выявленные сильные стороны кандидата"
    )
    weaknesses: List[str] = Field(
        ..., 
        description="Выявленные слабые стороны кандидата"
    )
    red_flags: List[str] = Field(
        default_factory=list, 
        description="Красные флаги (критические проблемы)"
    )
    cultural_fit_score: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="Оценка соответствия культуре компании 1-5"
    )
    
    @property
    def average_competency_score(self) -> float:
        """Средняя оценка по всем компетенциям."""
        if not self.competency_scores:
            return 0.0
        return sum(cs.score for cs in self.competency_scores) / len(self.competency_scores)


class CandidateProfile(BaseModel):
    """Профиль кандидата, извлеченный автоматически из резюме.
    
    Результат интеллектуального анализа резюме для определения
    уровня, роли и ключевых характеристик кандидата.
    """
    detected_level: CandidateLevel = Field(
        ..., 
        description="Автоматически определенный уровень кандидата"
    )
    detected_role: ITRole = Field(
        ..., 
        description="Автоматически определенная IT-роль"
    )
    years_of_experience: Optional[int] = Field(
        None, 
        description="Количество лет опыта работы"
    )
    key_technologies: List[str] = Field(
        default_factory=list, 
        description="Ключевые технологии и навыки из резюме"
    )
    education_level: Optional[str] = Field(
        None, 
        description="Уровень образования"
    )
    previous_companies: List[str] = Field(
        default_factory=list, 
        description="Предыдущие места работы"
    )
    management_experience: bool = Field(
        False, 
        description="Есть ли опыт управления людьми/проектами"
    )


class InterviewConfiguration(BaseModel):
    """Конфигурация проведения интервью.
    
    Параметры, определяющие как будет проводиться симуляция интервью
    в зависимости от профиля кандидата и требований позиции.
    """
    target_rounds: int = Field(
        default=5, 
        ge=3, 
        le=7, 
        description="Целевое количество раундов интервью"
    )
    focus_areas: List[CompetencyArea] = Field(
        default_factory=list, 
        description="Приоритетные области для оценки"
    )
    include_behavioral: bool = Field(
        True, 
        description="Включать поведенческие вопросы (STAR)"
    )
    include_technical: bool = Field(
        True, 
        description="Включать технические вопросы"
    ) 
    difficulty_level: Literal["easy", "medium", "hard"] = Field(
        "medium", 
        description="Уровень сложности вопросов"
    )


class InterviewSimulation(BaseModel):
    """Результат полной симуляции интервью между HR и кандидатом.
    
    Основная модель данных, содержащая весь процесс интервью от начала
    до итоговой оценки и рекомендаций. Это то, что возвращает LLM генератор.
    """
    # Базовая информация о симуляции
    position_title: str = Field(
        ..., 
        description="Название позиции для которой проводится интервью"
    )
    candidate_name: str = Field(
        ..., 
        description="Имя кандидата"
    )
    company_context: str = Field(
        ..., 
        description="Контекст компании и позиции"
    )
    
    # Профиль и конфигурация
    candidate_profile: CandidateProfile = Field(
        ..., 
        description="Автоматически определенный профиль кандидата"
    )
    interview_config: InterviewConfiguration = Field(
        ..., 
        description="Конфигурация проведенного интервью"
    )
    
    # Основной диалог
    dialog_messages: List[DialogMessage] = Field(
        ..., 
        description="Полный диалог в хронологическом порядке"
    )
    
    # Результаты профессиональной оценки
    assessment: InterviewAssessment = Field(
        ..., 
        description="Детальная оценка результатов интервью"
    )
    
    # Текстовые рекомендации (для совместимости с existing системами)
    hr_assessment: str = Field(
        ..., 
        description="Итоговая текстовая оценка от HR-менеджера"
    )
    candidate_performance_analysis: str = Field(
        ..., 
        description="Детальный анализ выступления кандидата"
    )
    improvement_recommendations: str = Field(
        ..., 
        description="Конкретные рекомендации кандидату по улучшению"
    )
    
    # Метаданные симуляции
    simulation_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Технические метаданные процесса симуляции"
    )
    
    @property
    def total_rounds_completed(self) -> int:
        """Общее количество завершенных раундов диалога."""
        if not self.dialog_messages:
            return 0
        return max((msg.round_number for msg in self.dialog_messages), default=0)
    
    @property
    def average_response_quality(self) -> float:
        """Средняя оценка качества ответов кандидата."""
        candidate_scores = [
            msg.response_quality for msg in self.dialog_messages 
            if msg.speaker == "Candidate" and msg.response_quality is not None
        ]
        return sum(candidate_scores) / len(candidate_scores) if candidate_scores else 0.0
    
    @property
    def covered_question_types(self) -> List[QuestionType]:
        """Типы вопросов, которые были заданы в интервью."""
        return list(set(
            msg.question_type for msg in self.dialog_messages 
            if msg.speaker == "HR" and msg.question_type is not None
        ))
    
    class Config:
        """Конфигурация Pydantic модели."""
        extra = "forbid"
        title = "InterviewSimulation"
        use_enum_values = True
        
        schema_extra = {
            "example": {
                "position_title": "Python Developer",
                "candidate_name": "Иван Иванов",
                "company_context": "Интервью на позицию Python Developer в IT компании",
                "candidate_profile": {
                    "detected_level": "middle",
                    "detected_role": "developer",
                    "years_of_experience": 3,
                    "key_technologies": ["Python", "Django", "PostgreSQL"],
                    "management_experience": False
                },
                "dialog_messages": [
                    {
                        "speaker": "HR",
                        "message": "Расскажите о себе и своем опыте разработки",
                        "round_number": 1,
                        "question_type": "introduction"
                    },
                    {
                        "speaker": "Candidate", 
                        "message": "Я разработчик с 3-летним опытом...",
                        "round_number": 1,
                        "response_quality": 4
                    }
                ]
            }
        }