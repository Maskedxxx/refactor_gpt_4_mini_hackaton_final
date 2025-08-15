# src/llm_cover_letter/options.py
# --- agent_meta ---
# role: llm-cover-letter-options
# owner: @backend
# contract: Параметры генерации сопроводительного письма и дефолтные значения
# last_reviewed: 2025-08-10
# interfaces:
#   - CoverLetterOptions
# --- /agent_meta ---

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import Field

from src.llm_features.base.options import BaseLLMOptions
from .models import RoleType


class CoverLetterOptions(BaseLLMOptions):
    """Опции генерации письма, настраиваемые снаружи."""

    role_hint: Optional[RoleType] = Field(
        None, description="Подсказка роли для промпта"
    )
    language: Literal["ru", "en"] = Field(
        "ru", description="Язык генерируемого письма"
    )
    length: Literal["SHORT", "MEDIUM", "LONG"] = Field(
        "LONG", description="Желаемая длина письма"
    )
    # Переопределяем дефолты из BaseLLMOptions
    temperature: float = Field(0.4, ge=0.0, le=2.0, description="Температура LLM")
    prompt_version: str = Field(
        "cover_letter.v1", description="Версия шаблона промпта"
    )
    quality_checks: bool = Field(False, description="Включить проверку качества письма")
    extra_context: Optional[dict[str, Any]] = Field(None, description="Произвольные дополнительные сигналы в промпт")

    class Config:
        extra = "allow"  # Наследуем от BaseLLMOptions, который поддерживает дополнительные поля
        title = "CoverLetterOptions"
