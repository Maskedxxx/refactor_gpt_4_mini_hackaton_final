# src/models/__init__.py
# --- agent_meta ---
# role: domain-models-package
# owner: @backend
# contract: Пакет доменных моделей (резюме, вакансии)
# last_reviewed: 2025-08-10
# --- /agent_meta ---

from .resume_models import ResumeInfo
from .vacancy_models import VacancyInfo

__all__ = [
    "ResumeInfo",
    "VacancyInfo",
]

