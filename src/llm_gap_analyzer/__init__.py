# src/llm_gap_analyzer/__init__.py
# --- agent_meta ---
# role: llm-gap-analyzer-package
# owner: @backend
# contract: Пакет фичи GAP-анализатора; авто-регистрация при импорте
# last_reviewed: 2025-08-15
# interfaces:
#   - LLMGapAnalyzerGenerator
#   - GapAnalyzerOptions
#   - register_gap_analyzer_feature()
# --- /agent_meta ---

from .service import LLMGapAnalyzerGenerator
from .options import GapAnalyzerOptions
from .bootstrap import register_gap_analyzer_feature

# Автоматическая регистрация фичи при импорте пакета
try:
    register_gap_analyzer_feature()
except Exception:
    # Безопасный импорт даже без настроек окружения
    pass

__all__ = [
    "LLMGapAnalyzerGenerator",
    "GapAnalyzerOptions",
    "register_gap_analyzer_feature",
]

