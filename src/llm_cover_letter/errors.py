# src/llm_cover_letter/errors.py
# --- agent_meta ---
# role: llm-cover-letter-errors
# owner: @backend
# contract: Исключения уровня домена для компонента сопроводительных писем
# last_reviewed: 2025-08-10
# interfaces:
#   - CoverLetterError
#   - QualityValidationError
#   - PromptBuildError
# --- /agent_meta ---

class CoverLetterError(Exception):
    """Базовая ошибка компонента сопроводительных писем."""


class QualityValidationError(CoverLetterError):
    """Письмо не прошло доменную проверку качества."""


class PromptBuildError(CoverLetterError):
    """Ошибка построения промпта/контекста."""
