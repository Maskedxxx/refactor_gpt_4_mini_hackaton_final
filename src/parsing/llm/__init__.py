# src/parsing/llm/__init__.py
# --- agent_meta ---
# role: llm-subpackage
# owner: @backend
# contract: Подпакет абстракции LLM
# last_reviewed: 2025-08-10
# --- /agent_meta ---

from .client import LLMClient, OpenAILLMClient
from .prompt import Prompt, PromptTemplate

__all__ = [
    "LLMClient",
    "OpenAILLMClient",
    "Prompt",
    "PromptTemplate",
]

