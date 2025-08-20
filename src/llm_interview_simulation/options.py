# src/llm_interview_simulation/options.py
# --- agent_meta ---
# role: interview-simulation-options
# owner: @backend
# contract: Опции для настройки симуляции интервью, наследующие BaseLLMOptions
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewSimulationOptions (extends BaseLLMOptions)
# --- /agent_meta ---

from __future__ import annotations

# Порядок переопределения (старший → младший):
# 1) Этот файл (InterviewSimulationOptions) — явные опции рантайма
# 2) config.yml — внешние шаблоны/настройки (если применимо)
# 3) config.py (default_settings) — встроенные дефолты/маппинги
# Примечание: опции управляют поведением генерации (temperature, tokens, личности и т.д.),
# но не подменяют сами тексты шаблонов; шаблоны берутся из YAML с fallback на код.

from typing import Optional, Literal, List, Callable, Awaitable
from pydantic import BaseModel, Field

from src.llm_features.base.options import BaseLLMOptions
from .models import CompetencyArea


class InterviewSimulationOptions(BaseLLMOptions):
    """Опции для настройки симуляции интервью.
    
    Расширяет базовые опции LLM Features Framework специфичными
    настройками для проведения симулированных интервью.
    """
    
    # === Основные параметры симуляции ===
    
    target_rounds: int = Field(
        default=5,
        ge=3,
        le=7,
        description="Количество раундов диалога в интервью (3-7)"
    )
    
    difficulty_level: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description="Уровень сложности вопросов: easy=junior, medium=middle, hard=senior+"
    )
    
    # === Типы вопросов ===
    
    include_behavioral: bool = Field(
        default=True,
        description="Включать поведенческие вопросы (STAR методика)"
    )
    
    include_technical: bool = Field(
        default=True,
        description="Включать технические вопросы"
    )
    
    include_leadership: Optional[bool] = Field(
        default=None,  # Автоматически определяется по уровню кандидата
        description="Включать вопросы на лидерство (None=автоопределение)"
    )
    
    # === Фокус интервью ===
    
    focus_areas: Optional[List[CompetencyArea]] = Field(
        default=None,
        description="Приоритетные области для оценки (None=автоопределение)"
    )
    
    # === Качество логирования ===
    
    # === Настройки генерации ===
    
    hr_personality: Literal["supportive", "neutral", "challenging"] = Field(
        default="neutral",
        description="Стиль поведения HR: supportive=поддерживающий, challenging=строгий"
    )
    
    candidate_confidence: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Уровень уверенности кандидата в ответах"
    )
    
    # === Технические настройки ===
    
    temperature_hr: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperature для генерации вопросов HR (0.7=сбалансированный)"
    )
    
    temperature_candidate: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Temperature для генерации ответов кандидата (0.8=более живой)"
    )
    
    max_tokens_per_message: int = Field(
        default=2500,
        ge=500,
        le=4000,
        description="Максимальное количество токенов на одно сообщение"
    )
    
    # === Колбэки и мониторинг ===
    
    enable_progress_callbacks: bool = Field(
        default=False,
        description="Включить колбэки для отслеживания прогресса"
    )
    
    log_detailed_prompts: bool = Field(
        default=False,
        description="Логировать детальные промпты для отладки"
    )
    
    # === Переопределение базовых опций ===
    
    # Устанавливаем более консервативные значения для интервью
    temperature: float = Field(
        default=0.7,
        description="Основная temperature (переопределяет базовую)"
    )
    
    max_tokens: int = Field(
        default=2500,
        description="Основной max_tokens (переопределяет базовый)"
    )
    
    class Config:
        """Конфигурация Pydantic модели."""
        extra = "forbid"
        title = "InterviewSimulationOptions"
        
        schema_extra = {
            "example": {
                "prompt_version": "v1.0",
                "target_rounds": 5,
                "difficulty_level": "medium",
                "include_behavioral": True,
                "include_technical": True,
                "hr_personality": "neutral",
                "candidate_confidence": "medium",
                "temperature_hr": 0.7,
                "temperature_candidate": 0.8,
            }
        }


class InterviewProgressCallback(BaseModel):
    """Модель для callback функции отслеживания прогресса.
    
    Используется для уведомления о ходе выполнения симуляции интервью.
    """
    
    current_round: int = Field(
        ...,
        description="Текущий раунд диалога"
    )
    
    total_rounds: int = Field(
        ...,
        description="Общее количество планируемых раундов"
    )
    
    current_stage: Literal[
        "analyzing_profile", 
        "generating_question", 
        "generating_answer", 
        "generating_question",
        "generating_answer"
    ] = Field(
        ...,
        description="Текущая стадия обработки"
    )
    
    stage_description: str = Field(
        ...,
        description="Описание текущей стадии для пользователя"
    )
    
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Процент выполнения (0-100)"
    )


# Типы для колбэков (для type hints в service.py)
ProgressCallbackType = Optional[Callable[[int, int], Awaitable[None]]]
DetailedProgressCallbackType = Optional[Callable[[InterviewProgressCallback], Awaitable[None]]]
