# src/llm_features/base/interfaces.py
# --- agent_meta ---
# role: llm-features-interfaces
# owner: @backend
# contract: Интерфейсы и протоколы для LLM-фич
# last_reviewed: 2025-08-15
# interfaces:
#   - ILLMGenerator (основной протокол генераторов)
#   - IFeatureValidator (протокол валидаторов)
#   - IFeatureFormatter (протокол форматтеров)
# --- /agent_meta ---

from __future__ import annotations

from typing import Protocol, Any, TypeVar
from abc import abstractmethod

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from .options import BaseLLMOptions

# TypeVar для результата генерации
T = TypeVar('T')


class ILLMGenerator(Protocol[T]):
    """Основной интерфейс для всех LLM-генераторов фич."""
    
    @abstractmethod
    async def generate(
        self, 
        resume: ResumeInfo, 
        vacancy: VacancyInfo, 
        options: BaseLLMOptions
    ) -> T:
        """Сгенерировать результат для данного резюме и вакансии."""
        ...
    
    @abstractmethod
    def get_feature_name(self) -> str:
        """Вернуть название фичи."""
        ...
    
    @abstractmethod
    def get_supported_versions(self) -> list[str]:
        """Вернуть список поддерживаемых версий."""
        ...


class IFeatureValidator(Protocol):
    """Протокол для валидаторов фич."""
    
    @abstractmethod
    def validate(
        self, 
        result: Any, 
        resume: ResumeInfo = None, 
        vacancy: VacancyInfo = None
    ) -> None:
        """Валидировать результат генерации."""
        ...


class IFeatureFormatter(Protocol):
    """Протокол для форматтеров фич."""
    
    @abstractmethod
    def format_resume_for_prompt(self, resume: ResumeInfo) -> str:
        """Форматировать резюме для промпта."""
        ...
    
    @abstractmethod  
    def format_vacancy_for_prompt(self, vacancy: VacancyInfo) -> str:
        """Форматировать вакансию для промпта."""
        ...