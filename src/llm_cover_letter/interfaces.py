# --- agent_meta ---
# role: llm-cover-letter-interface
# owner: @backend
# contract: Публичный интерфейс генератора сопроводительных писем
# last_reviewed: 2025-08-10
# interfaces:
#   - ILetterGenerator.generate(resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions) -> EnhancedCoverLetter
#   - ILetterGenerator.format_for_email(letter: EnhancedCoverLetter) -> str
# --- /agent_meta ---

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo

from .models import EnhancedCoverLetter
from .options import CoverLetterOptions


class ILetterGenerator(Protocol):
    """Контракт на генерацию сопроводительных писем."""

    async def generate(
        self, resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions
    ) -> EnhancedCoverLetter:  # pragma: no cover - интерфейс
        """Сгенерировать письмо на основе доменных моделей и опций."""
        ...

    def format_for_email(self, letter: EnhancedCoverLetter) -> str:  # pragma: no cover
        """Вернуть строку письма, готовую к отправке по email."""
        ...

