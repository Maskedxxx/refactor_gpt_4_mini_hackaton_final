# src/llm_features/config.py
# --- agent_meta ---
# role: llm-features-config
# owner: @backend
# contract: Базовая конфигурация для LLM-фич с поддержкой префиксов через Pydantic
# last_reviewed: 2025-08-15
# interfaces:
#   - BaseFeatureSettings (базовый класс настроек с env_prefix)
# --- /agent_meta ---

from __future__ import annotations

from typing import Optional
from pydantic import ConfigDict, Field

from pydantic_settings import BaseSettings


class BaseFeatureSettings(BaseSettings):
    """Базовые настройки для всех LLM-фич.
    
    Предоставляет общие настройки:
    - language: язык генерации
    - temperature: температура LLM
    - model_name: название модели
    - quality_checks: включить проверки качества
    """
    
    # Общие настройки LLM
    language: str = Field(default="ru", description="Язык генерации")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="Температура LLM")
    model_name: Optional[str] = Field(default=None, description="Название модели")
    
    # Промпт настройки
    prompt_version: str = Field(default="v1", description="Версия промпта")
    
    # Контроль качества
    quality_checks: bool = Field(default=False, description="Включить проверки качества")
    
    model_config = ConfigDict(
        env_file='.env',
        extra='ignore'
    )


# Пример использования для конкретной фичи:
#
# class CoverLetterSettings(BaseFeatureSettings):
#     # Специфичные для cover_letter настройки
#     length: str = Field(default="MEDIUM", description="Длина письма")
#     
#     model_config = ConfigDict(
#         env_file='.env',
#         env_prefix="COVER_LETTER_",
#         extra='ignore'
#     )