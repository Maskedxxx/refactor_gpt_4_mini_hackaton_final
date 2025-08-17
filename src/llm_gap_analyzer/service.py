# src/llm_gap_analyzer/service.py
# --- agent_meta ---
# role: llm-gap-analyzer-service
# owner: @backend
# contract: Генератор GAP-анализа на базе AbstractLLMGenerator (универсальное API фич)
# last_reviewed: 2025-08-15
# interfaces:
#   - LLMGapAnalyzerGenerator(AbstractLLMGenerator[EnhancedResumeTailoringAnalysis])
# --- /agent_meta ---

from __future__ import annotations

from typing import Optional, Dict, Any

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.prompt import Prompt
from src.llm_features.base.generator import AbstractLLMGenerator
from src.llm_features.base.options import BaseLLMOptions
from src.llm_features.prompts.versioning import get_template_registry

from .models import EnhancedResumeTailoringAnalysis
from .options import GapAnalyzerOptions
from .config import GapAnalyzerSettings
from .formatter import format_resume_data, format_vacancy_data
from .prompts.mappings import (
    extract_requirements_from_vacancy,
    build_skills_match_summary,
)


class LLMGapAnalyzerGenerator(AbstractLLMGenerator[EnhancedResumeTailoringAnalysis]):
    """Генератор GAP-анализа с использованием общей архитектуры фич."""

    def __init__(
        self,
        *,
        settings: Optional[GapAnalyzerSettings] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._settings = settings or GapAnalyzerSettings()

    async def _build_prompt(
        self,
        resume: ResumeInfo,
        vacancy: VacancyInfo,
        options: BaseLLMOptions,
    ) -> Prompt:
        # Рендерим блоки форматтера (он работает с dict)
        resume_block = format_resume_data(resume.model_dump())
        vacancy_block = format_vacancy_data(vacancy.model_dump())

        # Динамические блоки
        requirements_block = extract_requirements_from_vacancy(vacancy)

        skills_match_summary_block = ""
        include_summary = getattr(options, "include_skill_match_summary", None)
        if include_summary is None:
            include_summary = self._settings.include_skill_match_summary
        if include_summary:
            skills_match_summary_block = build_skills_match_summary(resume, vacancy)

        # Получаем шаблон из глобального реестра
        version = options.prompt_version or self._settings.prompt_version
        # В реестре версии без префикса имени фичи, поэтому нормализуем
        normalized_version = version.replace("gap_analyzer.", "") if version else None
        template = get_template_registry().get_template("gap_analyzer", version=normalized_version)

        # Формируем extra_context_block как в cover_letter
        extra_context = getattr(options, "extra_context", None) or {}
        if extra_context:
            extra_context_block = "\n".join(f"- {k}: {v}" for k, v in extra_context.items())
        else:
            extra_context_block = "(нет)"

        ctx: Dict[str, Any] = {
            "language": options.language or self._settings.language,
            "resume_block": resume_block,
            "vacancy_block": vacancy_block,
            "requirements_block": requirements_block,
            "skills_match_summary_block": skills_match_summary_block,
            "extra_context_block": extra_context_block,
        }

        return template.render(ctx)

    async def _call_llm(self, prompt: Prompt, options: BaseLLMOptions) -> EnhancedResumeTailoringAnalysis:
        return await self._llm.generate_structured(
            prompt=prompt,
            schema=EnhancedResumeTailoringAnalysis,
            temperature=options.temperature or self._settings.temperature,
        )

    def _merge_with_defaults(self, options: BaseLLMOptions) -> BaseLLMOptions:
        if isinstance(options, GapAnalyzerOptions):
            defaults = {
                "language": self._settings.language,
                "prompt_version": self._settings.prompt_version,
                "temperature": self._settings.temperature,
                "include_skill_match_summary": self._settings.include_skill_match_summary,
            }
            user = options.model_dump(exclude_unset=True)
            merged = {**defaults, **user}
            return GapAnalyzerOptions(**merged)
        else:
            return GapAnalyzerOptions(
                language=options.language or self._settings.language,
                prompt_version=options.prompt_version or self._settings.prompt_version,
                temperature=options.temperature or self._settings.temperature,
                quality_checks=options.quality_checks if options.quality_checks is not None else False,
                extra_context=getattr(options, 'extra_context', None),
            )

    def get_feature_name(self) -> str:
        return "gap_analyzer"

    def get_supported_versions(self) -> list[str]:
        # Версии в реестре регистрируются без префикса названия фичи
        return ["gap_analyzer.v1"]

