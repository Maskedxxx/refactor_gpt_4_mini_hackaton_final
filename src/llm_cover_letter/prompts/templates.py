# src/llm_cover_letter/prompts/templates.py
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
            "Учитывай контекст компании и позиции. Пиши на языке: {language}.\n\n"
            "## КОНТЕКСТ КОМПАНИИ\n"
            "Размер компании: {company_size}; Компания: {company_name}; Позиция: {position_title}.\n"
            "Желаемая длина: {length}.\n\n"
            "## ТОНАЛЬНОСТЬ\n"
            "{company_tone_instruction}\n\n"
            "## АДАПТАЦИЯ ПО РОЛИ\n"
            "{role_adaptation_instruction}"
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

    elif version == "cover_letter.v2":
        # Улучшенная версия с динамическими блоками
        system_tmpl = (
            "Ты — эксперт по написанию персонализированных сопроводительных писем в IT.\n"
            "Создавай профессиональные письма, адаптированные под контекст компании и роли.\n\n"
            "## КОНТЕКСТ ЗАДАЧИ\n"
            "Язык письма: {language}\n"
            "Компания: {company_name} (размер: {company_size})\n"
            "Позиция: {position_title}\n"
            "Желаемая длина: {length}\n\n"
            "## ТОНАЛЬНОСТЬ И СТИЛЬ\n"
            "{company_tone_instruction}\n\n"
            "## СПЕЦИАЛИЗАЦИЯ И ФОКУС\n"
            "{role_adaptation_instruction}\n\n"
            "## ТРЕБОВАНИЯ К КАЧЕСТВУ\n"
            "- Максимальная персонализация под компанию и роль\n"
            "- Конкретные примеры из опыта, релевантные позиции\n"
            "- Избегай общих фраз и шаблонности\n"
            "- Фокусируйся на ценности для работодателя\n"
            "- Учитывай размер компании в формулировках"
        )

        user_tmpl = (
            "## ИСХОДНЫЕ ДАННЫЕ\n\n"
            "### Профиль кандидата:\n"
            "<resume_start>\n{resume_block}\n</resume_end>\n\n"
            "### Целевая вакансия:\n"
            "<vacancy_start>\n{vacancy_block}\n</vacancy_end>\n\n"
            "### Дополнительный контекст:\n"
            "{extra_context_block}\n\n"
            "## ЗАДАЧА\n"
            "На основе данных создай JSON согласно схеме EnhancedCoverLetter.\n"
            "Учти все инструкции по тональности и адаптации под роль."
        )
        
        return PromptTemplate(
            name="cover_letter", version="v2", system_tmpl=system_tmpl, user_tmpl=user_tmpl
        )

    # fallback на v1
    return get_template("cover_letter.v1")
