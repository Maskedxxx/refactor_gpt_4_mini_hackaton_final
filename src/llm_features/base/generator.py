# src/llm_features/base/generator.py
# --- agent_meta ---
# role: llm-features-generator
# owner: @backend
# contract: Абстрактный генератор с базовой логикой для всех LLM-фич
# last_reviewed: 2025-08-15
# interfaces:
#   - AbstractLLMGenerator (базовая реализация ILLMGenerator)
# --- /agent_meta ---

from __future__ import annotations

import os
from abc import abstractmethod, ABC
from typing import Optional, TypeVar, Generic

from openai import OpenAI

from src.utils import get_logger
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.client import LLMClient, OpenAILLMClient
from src.parsing.llm.prompt import Prompt

from .interfaces import IFeatureValidator, IFeatureFormatter
from .options import BaseLLMOptions
from .errors import BaseLLMError

# TypeVar для типа результата
T = TypeVar('T')


class AbstractLLMGenerator(Generic[T], ABC):
    """Базовый класс для всех LLM-генераторов фич.
    
    Предоставляет:
    - Базовую логику инициализации LLM клиента
    - Стандартный workflow генерации
    - DI для компонентов (validator, formatter)
    - Логирование
    """
    
    def __init__(
        self,
        *,
        llm: Optional[LLMClient] = None,
        validator: Optional[IFeatureValidator] = None,
        formatter: Optional[IFeatureFormatter] = None,
        openai_api_key: Optional[str] = None,
        openai_model_name: Optional[str] = None,
    ) -> None:
        self._log = get_logger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Инициализация LLM клиента
        if llm is None:
            client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
            model_name = openai_model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini-2024-07-18")
            self._llm = OpenAILLMClient(client, default_model=model_name)
        else:
            self._llm = llm
        
        # DI компонентов
        self._validator = validator
        self._formatter = formatter
    
    async def generate(
        self, 
        resume: ResumeInfo, 
        vacancy: VacancyInfo, 
        options: BaseLLMOptions
    ) -> T:
        """Стандартный workflow генерации."""
        try:
            self._log.info(
                "Запуск генерации фичи %s, версия=%s", 
                self.get_feature_name(), 
                options.prompt_version
            )
            
            # 1. Подготовка опций с дефолтами
            merged_options = self._merge_with_defaults(options)
            
            # 2. Сборка промпта
            prompt = await self._build_prompt(resume, vacancy, merged_options)
            
            # 3. Вызов LLM
            result = await self._call_llm(prompt, merged_options)
            
            # 4. Валидация
            if merged_options.quality_checks and self._validator:
                self._validator.validate(result, resume=resume, vacancy=vacancy)
            
            self._log.info("Генерация фичи %s завершена успешно", self.get_feature_name())
            return result
            
        except Exception as e:
            self._log.error("Ошибка генерации фичи %s: %s", self.get_feature_name(), str(e))
            raise BaseLLMError(f"Generation failed for {self.get_feature_name()}: {str(e)}") from e
    
    @abstractmethod
    async def _build_prompt(
        self, 
        resume: ResumeInfo, 
        vacancy: VacancyInfo, 
        options: BaseLLMOptions
    ) -> Prompt:
        """Построить промпт для данной фичи."""
        ...
    
    @abstractmethod
    async def _call_llm(self, prompt: Prompt, options: BaseLLMOptions) -> T:
        """Вызвать LLM и получить структурированный результат."""
        ...
    
    @abstractmethod
    def _merge_with_defaults(self, options: BaseLLMOptions) -> BaseLLMOptions:
        """Слить пользовательские опции с дефолтами фичи."""
        ...
    
    @abstractmethod
    def get_feature_name(self) -> str:
        """Название фичи."""
        ...
    
    @abstractmethod
    def get_supported_versions(self) -> list[str]:
        """Поддерживаемые версии."""
        ...
    
    def format_for_output(self, result: T) -> str:
        """Форматировать результат для вывода (опционально переопределить)."""
        return str(result)