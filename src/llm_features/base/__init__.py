# src/llm_features/base/__init__.py
# --- agent_meta ---
# role: llm-features-base
# owner: @backend
# contract: Базовые компоненты для LLM-фич (интерфейсы, абстрактные классы, опции)
# last_reviewed: 2025-08-15
# --- /agent_meta ---

from .interfaces import ILLMGenerator
from .generator import AbstractLLMGenerator
from .options import BaseLLMOptions
from .errors import BaseLLMError

__all__ = [
    "ILLMGenerator",
    "AbstractLLMGenerator", 
    "BaseLLMOptions",
    "BaseLLMError",
]