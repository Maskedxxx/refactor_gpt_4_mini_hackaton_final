# src/llm_cover_letter/service.py
# --- agent_meta ---
# role: llm-cover-letter-service
# owner: @backend
# contract: Реализация генератора сопроводительных писем (DI: LLM, билдер контекста, билдер промпта)
# last_reviewed: 2025-08-10
# interfaces:
#   - LLMCoverLetterGenerator (implements ILetterGenerator)
# --- /agent_meta ---

from __future__ import annotations

from typing import Optional

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.client import LLMClient
from src.parsing.llm.prompt import Prompt
from src.llm_features.base.generator import AbstractLLMGenerator
from src.llm_features.base.interfaces import IFeatureValidator, IFeatureFormatter
from src.llm_features.base.options import BaseLLMOptions

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


class LLMCoverLetterGenerator(AbstractLLMGenerator[EnhancedCoverLetter], ILetterGenerator):
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
        # Инициализация базового класса
        super().__init__(
            llm=llm,
            validator=validator or DefaultCoverLetterValidator(),
            openai_api_key=openai_api_key,
            openai_model_name=openai_model_name
        )
        
        self._settings = settings or LLMCoverLetterSettings()
        self._context_builder = context_builder or DefaultContextBuilder()
        self._prompt_builder = prompt_builder or DefaultPromptBuilder()

    # Реализация абстрактных методов из AbstractLLMGenerator
    
    async def _build_prompt(
        self, 
        resume: ResumeInfo, 
        vacancy: VacancyInfo, 
        options: BaseLLMOptions
    ) -> Prompt:
        """Построить промпт для cover letter."""
        # Контекст
        ctx = self._context_builder.build(resume, vacancy, options)
        resume_block = format_resume_for_cover_letter(resume)
        vacancy_block = format_vacancy_for_cover_letter(vacancy)

        # Промпт
        return self._prompt_builder.build(
            resume_block=resume_block, vacancy_block=vacancy_block, ctx=ctx, options=options
        )
    
    async def _call_llm(self, prompt: Prompt, options: BaseLLMOptions) -> EnhancedCoverLetter:
        """Вызвать LLM и получить результат."""
        return await self._llm.generate_structured(
            prompt=prompt, 
            schema=EnhancedCoverLetter, 
            temperature=options.temperature
        )
    
    def _merge_with_defaults(self, options: BaseLLMOptions) -> BaseLLMOptions:
        """Слить пользовательские опции с дефолтами фичи."""
        # Если переданы CoverLetterOptions, используем их
        if isinstance(options, CoverLetterOptions):
            return CoverLetterOptions(
                **{
                    "language": self._settings.language,
                    "prompt_version": self._settings.prompt_version,
                    "temperature": self._settings.temperature,
                    "quality_checks": self._settings.quality_checks,
                },
                **options.model_dump(exclude_unset=True),
            )
        else:
            # Fallback для BaseLLMOptions
            return CoverLetterOptions(
                language=options.language or self._settings.language,
                prompt_version=options.prompt_version or self._settings.prompt_version,
                temperature=options.temperature or self._settings.temperature,
                quality_checks=options.quality_checks if options.quality_checks is not None else self._settings.quality_checks,
                extra_context=options.extra_context,
            )
    
    def get_feature_name(self) -> str:
        """Название фичи."""
        return "cover_letter"
    
    def get_supported_versions(self) -> list[str]:
        """Поддерживаемые версии."""
        return ["cover_letter.v1", "cover_letter.v2"]
    
    # Backward compatibility методы
    
    async def generate(self, resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions) -> EnhancedCoverLetter:
        """Основной метод генерации (backward compatibility)."""
        # Используем новую архитектуру через AbstractLLMGenerator
        return await super().generate(resume, vacancy, options)

    def format_for_email(self, letter: EnhancedCoverLetter) -> str:
        return format_letter_for_email_text(letter)
