# --- agent_meta ---
# role: llm-cover-letter-service
# owner: @backend
# contract: Реализация генератора сопроводительных писем (DI: LLM, билдер контекста, билдер промпта)
# last_reviewed: 2025-08-10
# interfaces:
#   - LLMCoverLetterGenerator (implements ILetterGenerator)
# --- /agent_meta ---

from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from src.utils import get_logger
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.client import LLMClient, OpenAILLMClient

from .interfaces import ILetterGenerator
from .models import EnhancedCoverLetter
from .options import CoverLetterOptions
from .config import LLMCoverLetterSettings
from .prompts.builders import (
    IContextBuilder,
    IPromptBuilder,
    DefaultContextBuilder,
    DefaultPromptBuilder,
)
from .formatter import (
    format_resume_for_cover_letter,
    format_vacancy_for_cover_letter,
    format_letter_for_email_text,
)
from .validators import ICoverLetterValidator, DefaultCoverLetterValidator


class LLMCoverLetterGenerator(ILetterGenerator):
    """Генератор сопроводительных писем на базе LLM.

    DI зависимости:
      - llm: реализация LLMClient (по умолчанию OpenAI через env)
      - context_builder: построение контекстных переменных
      - prompt_builder: сборка system/user промптов
      - settings: дефолтные значения опций
    """

    def __init__(
        self,
        *,
        llm: Optional[LLMClient] = None,
        context_builder: Optional[IContextBuilder] = None,
        prompt_builder: Optional[IPromptBuilder] = None,
        settings: Optional[LLMCoverLetterSettings] = None,
        openai_api_key: Optional[str] = None,
        openai_model_name: Optional[str] = None,
        validator: Optional[ICoverLetterValidator] = None,
    ) -> None:
        self._log = get_logger(__name__)
        self._settings = settings or LLMCoverLetterSettings()

        if llm is None:
            client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
            model_name = (
                openai_model_name
                or self._settings.model_name
                or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini-2024-07-18")
            )
            self._llm = OpenAILLMClient(client, default_model=model_name)
        else:
            self._llm = llm

        self._context_builder = context_builder or DefaultContextBuilder()
        self._prompt_builder = prompt_builder or DefaultPromptBuilder()
        self._validator = validator or DefaultCoverLetterValidator()

    async def generate(
        self, resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions
    ) -> EnhancedCoverLetter:
        # Слияние опций с дефолтами
        opts = CoverLetterOptions(
            **{
                "language": self._settings.language,
                "prompt_version": self._settings.prompt_version,
                "temperature": self._settings.temperature,
                "quality_checks": self._settings.quality_checks,
            },
            **options.model_dump(exclude_unset=True),
        )

        # Контекст
        ctx = self._context_builder.build(resume, vacancy, opts)
        resume_block = format_resume_for_cover_letter(resume)
        vacancy_block = format_vacancy_for_cover_letter(vacancy)

        # Промпт
        prompt = self._prompt_builder.build(
            resume_block=resume_block, vacancy_block=vacancy_block, ctx=ctx, options=opts
        )

        # Вызов LLM (structured output)
        self._log.info(
            "Генерация сопроводительного письма: template=%s/%s",
            getattr(getattr(self._prompt_builder, "_template", None), "name", "cover_letter"),
            opts.prompt_version,
        )
        letter = await self._llm.generate_structured(
            prompt=prompt,
            schema=EnhancedCoverLetter,
            temperature=opts.temperature,
        )

        # Валидация качества (можно отключить через опции)
        if opts.quality_checks:
            self._validator.validate(letter, resume=resume, vacancy=vacancy)

        return letter

    def format_for_email(self, letter: EnhancedCoverLetter) -> str:
        return format_letter_for_email_text(letter)
