# src/llm_cover_letter/config.py
# --- agent_meta ---
# role: llm-cover-letter-settings
# owner: @backend
# contract: Настройки компонента сопроводительных писем (версия промпта, температура, проверки)
# last_reviewed: 2025-08-10
# interfaces:
#   - LLMCoverLetterSettings
# --- /agent_meta ---

from __future__ import annotations

from typing import Literal

from pydantic import Field, ConfigDict

from src.llm_features.config import BaseFeatureSettings


class LLMCoverLetterSettings(BaseFeatureSettings):
    """Конфигурация генератора сопроводительных писем.

    Environment:
      - COVER_LETTER_PROMPT_VERSION
      - COVER_LETTER_TEMPERATURE
      - COVER_LETTER_QUALITY_CHECKS
      - COVER_LETTER_LANGUAGE
      - COVER_LETTER_MODEL_NAME (опционально переопределяет LLM модель)
    """

    # Переопределяем дефолты для cover_letter
    prompt_version: str = Field(
        default="cover_letter.v2", description="Версия шаблона промпта"
    )
    temperature: float = Field(default=0.4, ge=0.0, le=2.0, description="Температура LLM")
    quality_checks: bool = Field(default=False, description="Включить проверки качества")
    language: Literal["ru", "en"] = Field(
        default="ru", description="Язык генерируемого письма"
    )
    
    # Специфичные для cover_letter настройки
    length: Literal["SHORT", "MEDIUM", "LONG"] = Field(
        default="MEDIUM", description="Желаемая длина письма"
    )

    model_config = ConfigDict(
        env_file=".env", env_prefix="COVER_LETTER_", extra="ignore"
    )
