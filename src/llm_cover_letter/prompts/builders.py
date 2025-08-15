# src/llm_cover_letter/prompts/builders.py
# --- agent_meta ---
# role: llm-cover-letter-prompt-builders
# owner: @backend
# contract: Интерфейсы и реализация сборщиков контекста и промптов для писем
# last_reviewed: 2025-08-10
# interfaces:
#   - IContextBuilder.build(resume, vacancy, options) -> dict
#   - IPromptBuilder.build(resume_block, vacancy_block, ctx, options) -> Prompt
# --- /agent_meta ---

from __future__ import annotations

from typing import Protocol

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.prompt import Prompt

from ..options import CoverLetterOptions
from .templates import get_template
from .mappings import (
    detect_role_from_title,
    get_company_tone_instruction,
    get_role_adaptation_instruction,
)
from ..formatter import format_cover_letter_context


class IContextBuilder(Protocol):
    def build(self, resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions) -> dict:
        """Построить словарь контекста для промпта (company_size, position_title, и пр.)."""
        ...


class DefaultContextBuilder:
    def build(self, resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions) -> dict:
        description = (vacancy.description or "").lower()
        company_size = "MEDIUM"
        if any(w in description for w in ["стартап", "startup", "молодая команда", "растущая команда"]):
            company_size = "STARTUP"
        elif any(w in description for w in ["корпорация", "холдинг", "группа компаний", "enterprise"]):
            company_size = "ENTERPRISE"
        elif any(w in description for w in ["международная", "global", "multinational", "мировой лидер"]):
            company_size = "LARGE"

        # Автоопределение role_hint из названия должности в резюме (если не задано пользователем)
        effective_role_hint = options.role_hint
        if not effective_role_hint and resume.title:
            detected_role = detect_role_from_title(resume.title)
            if detected_role:
                effective_role_hint = detected_role

        ctx = {
            "company_size": company_size,
            "company_name": vacancy.company_name,
            "position_title": vacancy.name,
            "language": options.language,
            "length": options.length,
            "role_hint": effective_role_hint.value if effective_role_hint else "",
            # Динамические блоки для промпта
            "company_tone_instruction": get_company_tone_instruction(company_size),
            "role_adaptation_instruction": get_role_adaptation_instruction(effective_role_hint) if effective_role_hint else "",
            # Сохраняем объекты для анализа в промпт-билдере
            "_resume": resume,
            "_vacancy": vacancy,
        }
        return ctx


class IPromptBuilder(Protocol):
    def build(self, *, resume_block: str, vacancy_block: str, ctx: dict, options: CoverLetterOptions,) -> Prompt:
        ...


class DefaultPromptBuilder:
    def build(
        self,
        *,
        resume_block: str,
        vacancy_block: str,
        ctx: dict,
        options: CoverLetterOptions,
    ) -> Prompt:
        # Получаем resume и vacancy из контекста для анализа
        resume = ctx.get('_resume')  
        vacancy = ctx.get('_vacancy')
        
        tmpl = get_template(options.prompt_version)
        context = dict(ctx)
        context["resume_block"] = resume_block
        context["vacancy_block"] = vacancy_block
        
        # Добавляем контекстный анализ если есть данные
        if resume and vacancy:
            context["context_analysis"] = format_cover_letter_context(resume, vacancy)
        else:
            context["context_analysis"] = ""
        
        # Дополнительный контекст из опций (dict | str | None)
        context["extra_context_block"] = (options.extra_context or {})
        
        # если extra_context_block словарь — превращаем в строку
        if isinstance(context["extra_context_block"], dict):
            if context["extra_context_block"]:
                kv = "\n".join(f"- {k}: {v}" for k, v in context["extra_context_block"].items())
                context["extra_context_block"] = kv
            else:
                context["extra_context_block"] = "(нет)"
        return tmpl.render(context)
