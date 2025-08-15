# src/llm_features/prompts/__init__.py
# --- agent_meta ---
# role: llm-features-prompts
# owner: @backend
# contract: Версионируемая система промптов для LLM-фич
# last_reviewed: 2025-08-15
# --- /agent_meta ---

from .versioning import VersionedPromptTemplate, PromptTemplateRegistry

__all__ = [
    "VersionedPromptTemplate",
    "PromptTemplateRegistry",
]