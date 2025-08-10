# src/parsing/llm/errors.py
# --- agent_meta ---
# role: llm-errors
# owner: @backend
# contract: Исключения для LLM-абстракции (вызовы, валидация)
# last_reviewed: 2025-08-10
# interfaces:
#   - LLMCallError
#   - SchemaValidationError
# --- /agent_meta ---

class LLMCallError(Exception):
    """Ошибка при вызове LLM провайдера (сеть, квоты, таймауты, 5xx)."""


class SchemaValidationError(Exception):
    """Ответ не соответствует ожидаемой схеме (response_format)."""
