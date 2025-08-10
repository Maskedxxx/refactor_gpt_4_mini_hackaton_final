# src/parsing/llm/client.py
# --- agent_meta ---
# role: llm-client
# owner: @backend
# contract: Абстракция LLM-клиента и адаптер OpenAI с поддержкой structured output (Pydantic)
# last_reviewed: 2025-08-10
# interfaces:
#   - LLMClient.generate_structured(prompt: Prompt, schema: type[BaseModel], ...) -> BaseModel
#   - OpenAILLMClient (реализация поверх openai-python >=1.x)
# --- /agent_meta ---

from __future__ import annotations

from typing import Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError
from src.utils import get_logger

from .prompt import Prompt
from .errors import LLMCallError, SchemaValidationError


T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """
    Контракт для LLM клиента, поддерживающего structured output через Pydantic схемы.
    """

    async def generate_structured(
        self,
        prompt: Prompt,
        schema: Type[T],
        *,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> T:  # pragma: no cover - интерфейс
        raise NotImplementedError


class OpenAILLMClient(LLMClient):
    """
    Реализация LLMClient поверх OpenAI API (openai-python >= 1.0) с parse API.
    """

    def __init__(self, client, default_model: str) -> None:
        # client: openai.OpenAI instance
        self._client = client
        self._default_model = default_model
        self._log = get_logger(__name__)

    async def generate_structured(
        self,
        prompt: Prompt,
        schema: Type[T],
        *,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> T:
        model = model_name or self._default_model
        try:
            self._log.info("LLM generate_structured: model=%s", model)
            self._log.debug(
                "Prompt lengths: system=%d, user=%d",
                len(prompt.system or ""),
                len(prompt.user or ""),
            )
            # openai-python SDK не async; вызываем синхронно в текущем потоке.
            # Для реального продакшена можно вынести в threadpool.
            completion = self._client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": prompt.system},
                    {"role": "user", "content": prompt.user},
                ],
                response_format=schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:  # сеть/квоты/таймауты и пр.
            self._log.error("LLMCallError: %s", e)
            raise LLMCallError(str(e)) from e

        msg = completion.choices[0].message
        parsed = getattr(msg, "parsed", None)
        if parsed is None:
            self._log.error("SchemaValidationError: parsed is None")
            raise SchemaValidationError("LLM вернул пустой parsed результат")
        try:
            # parsed уже экземпляр pydantic модели в OpenAI SDK, но оставим валидацию на всякий случай
            result = schema.model_validate(parsed)
            self._log.info("LLM structured output parsed successfully: %s", schema.__name__)
            return result
        except ValidationError as ve:
            self._log.error("SchemaValidationError: %s", ve)
            raise SchemaValidationError(str(ve)) from ve
