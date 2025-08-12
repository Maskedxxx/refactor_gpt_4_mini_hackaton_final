# --- agent_meta ---
# role: llm-cover-letter-validator
# owner: @backend
# contract: Контракт и стандартная валидация качества сопроводительного письма
# last_reviewed: 2025-08-10
# interfaces:
#   - ICoverLetterValidator.validate(letter, resume, vacancy) -> None | raises QualityValidationError
# --- /agent_meta ---

from __future__ import annotations

from typing import Protocol

from .errors import QualityValidationError
from .models import EnhancedCoverLetter
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo


class ICoverLetterValidator(Protocol):
    def validate(self, letter: EnhancedCoverLetter, *, resume: ResumeInfo, vacancy: VacancyInfo) -> None:
        ...


class DefaultCoverLetterValidator(ICoverLetterValidator):
    def validate(self, letter: EnhancedCoverLetter, *, resume: ResumeInfo, vacancy: VacancyInfo) -> None:
        # Простейшие эвристики качества, расширим по мере необходимости
        company_name = (vacancy.company_name or "").lower()
        full_text = " ".join(
            [letter.opening_hook, letter.company_interest, letter.relevant_experience]
        ).lower()

        checks = [
            (not company_name) or (company_name in full_text),
            letter.personalization_score >= 6,
            letter.professional_tone_score >= 7,
            letter.relevance_score >= 6,
            len(letter.skills_match.matched_skills) >= 1,
            len(letter.personalization.value_proposition) >= 30,
        ]
        if not all(checks):
            raise QualityValidationError("Сопроводительное письмо не прошло проверку качества")

