# src/llm_gap_analyzer/prompts/templates.py
# --- agent_meta ---
# role: llm-gap-analyzer-prompts
# owner: @backend
# contract: Шаблоны system/user промптов для GAP-анализатора
# last_reviewed: 2025-08-15
# interfaces:
#   - get_template(version: str) -> PromptTemplate
# --- /agent_meta ---

from __future__ import annotations

from src.parsing.llm.prompt import PromptTemplate


def get_template(version: str) -> PromptTemplate:
    """Вернуть шаблон промпта по версии для gap_analyzer.

    Версия по умолчанию: gap_analyzer.v1
    """
    if version == "gap_analyzer.v1":
        system_tmpl = (
            "# РОЛЬ: Ты — эксперт HR с 10+ летним опытом GAP-анализа резюме в IT-сфере\n\n"
            "## КОНТЕКСТ ЗАДАЧИ\n"
            "Ты проводишь профессиональный GAP-анализ резюме кандидата относительно конкретной вакансии.\n"
            "Твоя задача — имитировать реальный процесс оценки, который используют опытные рекрутеры.\n\n"
            "## МЕТОДОЛОГИЯ АНАЛИЗА (следуй строго по этапам)\n\n"
            "### ЭТАП 1: ПЕРВИЧНЫЙ СКРИНИНГ (7-15 секунд) → PrimaryScreeningResult\n"
            "- Соответствие должности → job_title_match\n"
            "- Общий стаж vs требуемый → experience_years_match\n"
            "- Наличие критичных навыков → key_skills_visible\n"
            "- Локация/готовность → location_suitable\n"
            "- Зарплатные ожидания vs бюджет → salary_expectations_match\n\n"
            "### ЭТАП 2: КЛАССИФИКАЦИЯ ТРЕБОВАНИЙ → RequirementAnalysis.requirement_type\n"
            "- MUST_HAVE | NICE_TO_HAVE | ADDITIONAL_BONUS\n\n"
            "### ЭТАП 3: ДЕТАЛЬНЫЙ АНАЛИЗ СООТВЕТСТВИЯ → RequirementAnalysis.compliance_status\n"
            "- FULL_MATCH | PARTIAL_MATCH | MISSING | UNCLEAR\n\n"
            "### ЭТАП 4: АНАЛИЗ КАЧЕСТВА ПРЕЗЕНТАЦИИ → ResumeQualityAssessment\n"
            "- structure_clarity, content_relevance, achievement_focus, adaptation_quality (1-10)\n\n"
            "## ФОРМАТ РЕКОМЕНДАЦИЙ → DetailedRecommendation\n"
            "- criticality: CRITICAL → critical_recommendations; IMPORTANT → important_recommendations; DESIRED → optional_recommendations\n\n"
            "{enum_guidance_block}\n"
        )

        user_tmpl = (
            "<resume_data>\n{resume_block}\n</resume_data>\n\n"
            "<vacancy_data>\n{vacancy_block}\n</vacancy_data>\n\n"
            "{requirements_block}\n\n"
            "{skills_match_summary_block}\n\n"
            "## ИНСТРУКЦИЯ ДЛЯ GAP-АНАЛИЗА\n\n"
            "Проведи анализ по этапам (1-5) и верни JSON строго по схеме EnhancedResumeTailoringAnalysis.\n"
        )

        return PromptTemplate(
            name="gap_analyzer", version="v1", system_tmpl=system_tmpl, user_tmpl=user_tmpl
        )

    # fallback на v1
    return get_template("gap_analyzer.v1")

