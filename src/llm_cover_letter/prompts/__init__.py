# src/llm_cover_letter/prompts/__init__.py
# --- agent_meta ---
# role: llm-cover-letter-prompts-package
# owner: @backend
# contract: Пакет промптов для сопроводительных писем
# last_reviewed: 2025-08-14
# --- /agent_meta ---

from .builders import DefaultContextBuilder, DefaultPromptBuilder
from .templates import get_template
from .mappings import (
    detect_role_from_title,
    get_company_tone_instruction, 
    get_role_adaptation_instruction
)

__all__ = [
    "DefaultContextBuilder",
    "DefaultPromptBuilder", 
    "get_template",
    "detect_role_from_title",
    "get_company_tone_instruction",
    "get_role_adaptation_instruction",
]