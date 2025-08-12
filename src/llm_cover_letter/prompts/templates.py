# --- agent_meta ---
# role: llm-cover-letter-prompts
# owner: @backend
# contract: Версионируемые шаблоны системного и пользовательского промптов для писем
# last_reviewed: 2025-08-10
# interfaces:
#   - get_template(version: str) -> PromptTemplate
# --- /agent_meta ---

from __future__ import annotations

from src.parsing.llm.prompt import PromptTemplate


def get_template(version: str) -> PromptTemplate:
    """Вернуть шаблон промпта по версии.

    Версия по умолчанию: cover_letter.v1
    """
    if version == "cover_letter.v1":
        system_tmpl = (
            "Ты — эксперт по написанию персонализированных сопроводительных писем в IT.\n"
            "Учитывай контекст компании и позиции. Пиши на языке: {language}.\n"
            "Размер компании: {company_size}; Компания: {company_name}; Позиция: {position_title}.\n"
            "Желаемая длина: {length}. Если передан role_hint: {role_hint}, адаптируй стиль."
        )

        user_tmpl = (
            "## Данные\n\n"
            "### Резюме:\n<resume_start>\n{resume_block}\n</resume_end>\n\n"
            "### Вакансия:\n<vacancy_start>\n{vacancy_block}\n</vacancy_end>\n\n"
            "### Доп. контекст:\n{extra_context_block}\n\n"
            "Сгенерируй JSON согласно схеме EnhancedCoverLetter."
        )
        return PromptTemplate(
            name="cover_letter", version="v1", system_tmpl=system_tmpl, user_tmpl=user_tmpl
        )

    # fallback на v1
    return get_template("cover_letter.v1")

