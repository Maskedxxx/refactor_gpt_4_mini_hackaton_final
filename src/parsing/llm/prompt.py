# src/parsing/llm/prompt.py
# --- agent_meta ---
# role: llm-prompt
# owner: @backend
# contract: Промпт-структуры и шаблоны для LLM задач
# last_reviewed: 2025-08-10
# interfaces:
#   - Prompt(system: str, user: str)
#   - PromptTemplate.render(context: dict) -> Prompt
# --- /agent_meta ---

from dataclasses import dataclass
from typing import Dict


@dataclass
class Prompt:
    system: str
    user: str


class PromptTemplate:
    """
    Простой шаблон промпта (system/user) с возможностью подстановки переменных.
    Имеет имя и версию для отслеживания изменений.
    """

    def __init__(self, name: str, version: str, system_tmpl: str, user_tmpl: str) -> None:
        self.name = name
        self.version = version
        self._system_tmpl = system_tmpl
        self._user_tmpl = user_tmpl

    def render(self, context: Dict[str, object]) -> Prompt:
        system = self._system_tmpl.format(**context)
        user = self._user_tmpl.format(**context)
        return Prompt(system=system, user=user)
