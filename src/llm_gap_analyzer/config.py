# src/llm_gap_analyzer/config.py
# --- agent_meta ---
# role: llm-gap-analyzer-config
# owner: @backend
# contract: Настройки фичи gap_analyzer через переменные окружения
# last_reviewed: 2025-08-15
# interfaces:
#   - GapAnalyzerSettings(BaseFeatureSettings)
# --- /agent_meta ---

from __future__ import annotations

from pydantic import Field, ConfigDict

from src.llm_features.config import BaseFeatureSettings


class GapAnalyzerSettings(BaseFeatureSettings):
    """Настройки GAP-анализатора из окружения."""

    # Специфичные дефолты
    prompt_version: str = Field(default="gap_analyzer.v1", description="Версия промпта для GAP анализатора")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Температура LLM для GAP")
    language: str = Field(default="ru", description="Язык анализа")
    include_skill_match_summary: bool = Field(default=True, description="Включать блок свода навыков")

    model_config = ConfigDict(
        env_file=".env",
        env_prefix="GAP_ANALYZER_",
        extra="ignore",
    )

