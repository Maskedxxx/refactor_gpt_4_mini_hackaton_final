# src/llm_cover_letter/__init__.py
# --- agent_meta ---
# role: llm-cover-letter
# owner: @backend
# contract: Публичные интерфейсы и модели для генерации сопроводительных писем (contract-first)
# last_reviewed: 2025-08-10
# interfaces:
#   - ILetterGenerator.generate(resume: ResumeInfo, vacancy: VacancyInfo, options: CoverLetterOptions) -> EnhancedCoverLetter
#   - ILetterGenerator.format_for_email(letter: EnhancedCoverLetter) -> str
#   - CoverLetterOptions
#   - EnhancedCoverLetter и связанные модели
# --- /agent_meta ---

from .interfaces import ILetterGenerator
from .service import LLMCoverLetterGenerator
from .models import (
    RoleType,
    CompanyContext,
    SkillsMatchAnalysis,
    PersonalizationStrategy,
    EnhancedCoverLetter,
)
from .options import CoverLetterOptions
from .errors import CoverLetterError, QualityValidationError, PromptBuildError
from .bootstrap import register_cover_letter_feature

# Автоматическая регистрация фичи при импорте модуля
try:
    register_cover_letter_feature()
except Exception:
    # Игнорируем ошибки регистрации (например, отсутствие OPENAI_API_KEY)
    pass

__all__ = [
    "ILetterGenerator",
    "LLMCoverLetterGenerator", 
    "CoverLetterOptions",
    "RoleType",
    "CompanyContext",
    "SkillsMatchAnalysis",
    "PersonalizationStrategy",
    "EnhancedCoverLetter",
    "CoverLetterError",
    "QualityValidationError",
    "PromptBuildError",
    "register_cover_letter_feature",
]
