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

        ctx = {
            "company_size": company_size,
            "company_name": vacancy.company_name,
            "position_title": vacancy.name,
            "language": options.language,
            "length": options.length,
            "role_hint": options.role_hint.value if options.role_hint else "",
        }
        # место для расширяемого контекста
        return ctx


class IPromptBuilder(Protocol):
    def build(
        self,
        *,
        resume_block: str,
        vacancy_block: str,
        ctx: dict,
        options: CoverLetterOptions,
    ) -> Prompt:
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
        tmpl = get_template(options.prompt_version)
        context = dict(ctx)
        context["resume_block"] = resume_block
        context["vacancy_block"] = vacancy_block
        context["extra_context_block"] = (options.extra_context or {}) or {}
        # если extra_context_block словарь — превращаем в строку
        if isinstance(context["extra_context_block"], dict):
            if context["extra_context_block"]:
                kv = "\n".join(f"- {k}: {v}" for k, v in context["extra_context_block"].items())
                context["extra_context_block"] = kv
            else:
                context["extra_context_block"] = "(нет)"
        return tmpl.render(context)
