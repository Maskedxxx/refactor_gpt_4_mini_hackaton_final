# src/llm_features/__init__.py
# --- agent_meta ---
# role: llm-features-core
# owner: @backend
# contract: Базовая архитектура для LLM-фич (registry, интерфейсы, базовые классы)
# last_reviewed: 2025-08-15
# interfaces:
#   - ILLMGenerator (протокол для всех фич)
#   - FeatureRegistry (управление фичами)
#   - AbstractLLMGenerator (базовая реализация)
# --- /agent_meta ---

from .registry import FeatureRegistry
from .base.interfaces import ILLMGenerator
from .base.generator import AbstractLLMGenerator
from .base.options import BaseLLMOptions
from .base.errors import BaseLLMError, FeatureNotFoundError, FeatureRegistrationError

__all__ = [
    "FeatureRegistry",
    "ILLMGenerator", 
    "AbstractLLMGenerator",
    "BaseLLMOptions",
    "BaseLLMError",
    "FeatureNotFoundError",
    "FeatureRegistrationError",
]