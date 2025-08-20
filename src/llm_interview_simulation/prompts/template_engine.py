# src/llm_interview_simulation/prompts/template_engine.py
# --- agent_meta ---
# role: interview-simulation-template-engine
# owner: @backend
# contract: Рендеринг Jinja2 шаблонов промптов из YAML для симуляции интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - render_template(template: str, context: dict) -> str
# --- /agent_meta ---

from __future__ import annotations

from typing import Any, Dict
from jinja2 import Environment, StrictUndefined, Undefined


class SilentUndefined(Undefined):
    """Безопасная undefined-переменная: возвращает пустую строку вместо исключений."""

    def _fail_with_undefined_error(self, *args, **kwargs):  # type: ignore[override]
        return ""


_env = Environment(trim_blocks=True, lstrip_blocks=True, undefined=SilentUndefined)


def render_template(template: str, context: Dict[str, Any]) -> str:
    """Рендерит Jinja2 шаблон с безопасными undefined и базовыми настройками.

    Args:
        template: строковый шаблон Jinja2
        context: словарь контекста

    Returns:
        str: отрендеренный текст
    """
    try:
        jtpl = _env.from_string(template or "")
        return jtpl.render(**(context or {}))
    except Exception:
        # В случае ошибки подстановки возвращаем сырой шаблон как fallback
        return template or ""

