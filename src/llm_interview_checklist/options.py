# src/llm_interview_checklist/options.py
# --- agent_meta ---
# role: llm-interview-checklist-options
# owner: @backend
# contract: Опции для генерации профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewChecklistOptions
# --- /agent_meta ---

from typing import Optional, List, Dict, Any
from pydantic import Field

from src.llm_features.base.options import BaseLLMOptions


class InterviewChecklistOptions(BaseLLMOptions):
    """
    Опции для генерации профессионального чек-листа подготовки к интервью.
    Наследует базовые параметры LLM и добавляет специфичные для подготовки к интервью.
    """
    
    # Специфичные параметры для подготовки к интервью
    focus_areas: Optional[List[str]] = Field(
        None, 
        description="Конкретные области фокуса (например, ['алгоритмы', 'системный дизайн', 'soft skills'])"
    )
    
    preparation_time_available: Optional[str] = Field(
        None, 
        description="Доступное время для подготовки (например, '1 неделя', '3 дня', '1 месяц')"
    )
    
    candidate_level_hint: Optional[str] = Field(
        None,
        description="Подсказка об уровне кандидата для более точной персонализации (JUNIOR, MIDDLE, SENIOR, LEAD)"
    )
    
    company_format_hint: Optional[str] = Field(
        None,
        description="Подсказка о формате компании (STARTUP, MEDIUM_COMPANY, LARGE_CORP, INTERNATIONAL)"
    )
    
    interview_format: Optional[str] = Field(
        None,
        description="Формат интервью (онлайн, офлайн, гибридный)"
    )
    
    # Переопределяем дефолты из BaseLLMOptions
    temperature: float = Field(0.2, description="Более консервативная температура для профессионального контента")
    prompt_version: str = Field("v1", description="Версия промпта для чек-листа")
    extra_context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст для персонализации")

    class Config:
        extra = "allow"  # Разрешаем дополнительные поля
        title = "InterviewChecklistOptions"