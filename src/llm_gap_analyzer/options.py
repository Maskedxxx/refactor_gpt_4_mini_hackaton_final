# src/llm_gap_analyzer/options.py
# --- agent_meta ---
# role: llm-gap-analyzer-options
# owner: @backend
# contract: Опции фичи gap_analyzer для управления генерацией
# last_reviewed: 2025-08-15
# interfaces:
#   - GapAnalyzerOptions(BaseLLMOptions)
# --- /agent_meta ---

from __future__ import annotations

from typing import Literal
from pydantic import Field

from src.llm_features.base.options import BaseLLMOptions


class GapAnalyzerOptions(BaseLLMOptions):
    """Опции для GAP-анализатора."""

    analysis_depth: Literal["screening", "full"] = Field(
        default="full", description="Глубина анализа: только скрининг или полный анализ"
    )
    include_skill_match_summary: bool = Field(
        default=True, description="Добавлять краткий свод совпадений/пробелов по навыкам"
    )

