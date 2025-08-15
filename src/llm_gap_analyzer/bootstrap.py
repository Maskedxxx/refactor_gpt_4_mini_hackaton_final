# src/llm_gap_analyzer/bootstrap.py
# --- agent_meta ---
# role: llm-gap-analyzer-bootstrap
# owner: @backend
# contract: Регистрация фичи gap_analyzer и её шаблонов промпта
# last_reviewed: 2025-08-15
# interfaces:
#   - register_gap_analyzer_templates() -> None
#   - register_gap_analyzer_feature() -> None
# --- /agent_meta ---

from src.llm_features.registry import get_global_registry
from src.llm_features.prompts.versioning import get_template_registry, VersionedPromptTemplate

from .prompts.templates import get_template
from .service import LLMGapAnalyzerGenerator


def register_gap_analyzer_templates() -> None:
    """Регистрация шаблонов promt'ов gap_analyzer в глобальном реестре."""
    template_registry = get_template_registry()

    v1_template = get_template("gap_analyzer.v1")
    template_registry.register_template(
        "gap_analyzer",
        "v1",
        VersionedPromptTemplate(
            feature_name="gap_analyzer",
            version="v1",
            system_template=v1_template._system_tmpl,
            user_template=v1_template._user_tmpl,
            description="GAP-анализ резюме относительно вакансии (v1)"
        ),
        set_as_default=True,
    )


def register_gap_analyzer_feature() -> None:
    """Регистрация фичи gap_analyzer в глобальном реестре."""
    registry = get_global_registry()

    # Сначала шаблоны
    register_gap_analyzer_templates()

    # Затем сама фича и версия
    registry.register(
        name="gap_analyzer",
        generator_class=LLMGapAnalyzerGenerator,
        version="v1",
        set_as_default=True,
        description="Профессиональный GAP-анализ резюме относительно вакансии",
    )

