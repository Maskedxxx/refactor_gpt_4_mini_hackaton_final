# src/llm_features/base/options.py
# --- agent_meta ---
# role: llm-features-options
# owner: @backend
# contract: Базовые опции для всех LLM-фич
# last_reviewed: 2025-08-15
# interfaces:
#   - BaseLLMOptions (базовые настройки всех фич)
# --- /agent_meta ---

from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class BaseLLMOptions(BaseModel):
    """Базовые опции для всех LLM-фич."""
    
    # Общие LLM настройки
    temperature: Optional[float] = Field(default=0.3, description="Температура генерации")
    model_name: Optional[str] = Field(default=None, description="Название модели")
    
    # Промпт настройки
    language: Optional[str] = Field(default="ru", description="Язык генерации")
    prompt_version: Optional[str] = Field(default="v1", description="Версия промпта")
    
    # Контроль качества
    quality_checks: Optional[bool] = Field(default=False, description="Включить проверки качества")
    
    class Config:
        # Позволяет наследникам добавлять свои поля
        extra = "allow"