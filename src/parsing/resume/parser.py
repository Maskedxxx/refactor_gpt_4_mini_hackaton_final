# src/parsing/resume/parser.py
# --- agent_meta ---
# role: resume-parser
# owner: @backend
# contract: Парсинг PDF резюме в структуру ResumeInfo через LLM (OpenAI structured output)
# last_reviewed: 2025-08-10
# interfaces:
#   - IResumeParser.parse(src: str | Path | bytes) -> ResumeInfo
#   - LLMResumeParser (экстракция PDF -> Prompt -> LLM -> ResumeInfo)
# --- /agent_meta ---

from __future__ import annotations

import os
from pathlib import Path
from typing import Union

from openai import OpenAI
from src.utils import get_logger

from src.models.resume_models import ResumeInfo
from src.parsing.llm.client import LLMClient, OpenAILLMClient
from src.parsing.llm.prompt import PromptTemplate
from src.parsing.resume.pdf_extractor import IPDFExtractor, PdfPlumberExtractor


class IResumeParser:
    async def parse(self, src: Union[str, Path, bytes]) -> ResumeInfo:  # pragma: no cover - интерфейс
        raise NotImplementedError


DEFAULT_SYSTEM_PROMPT = (
    """
    Ты опытный HR-специалист. Твоя задача - извлечь и структурировать информацию из текста резюме.
    Внимательно проанализируй предоставленный текст резюме и извлеки всю доступную информацию.
    Требования:
    1) Если информация не найдена, оставь поле пустым (None/[] в зависимости от типа)
    2) Для списков навыков (skill_set) выдели ключевые технические навыки
    3) Для experience заполни все доступные поля (описание, должность, компания, даты)
    4) Для education укажи все образование (основное и дополнительное)
    5) Для языков укажи названия и уровни владения
    6) Тщательно ищи контактную информацию и сайты
    7) Если зарплатные ожидания не указаны, не придумывай их
    8) Опыт работы в total_experience указывай в месяцах
    """
    .strip()
)

DEFAULT_USER_TMPL = "Проанализируй и структурируй это резюме:\n\n{resume_text}"


class LLMResumeParser(IResumeParser):
    """Парсер резюме на базе LLM.

    Поток:
    - экстракция текста из PDF (IPDFExtractor)
    - рендер промпта (PromptTemplate)
    - вызов LLM с response_format=ResumeInfo
    """
    def __init__(
        self,
        extractor: IPDFExtractor | None = None,
        llm: LLMClient | None = None,
        *,
        openai_api_key: str | None = None,
        openai_model_name: str | None = None,
        prompt_template: PromptTemplate | None = None,
    ) -> None:
        self._extractor = extractor or PdfPlumberExtractor()
        if llm is None:
            client = OpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
            model_name = openai_model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini-2024-07-18")
            self._llm = OpenAILLMClient(client, default_model=model_name)
        else:
            self._llm = llm

        self._template = (
            prompt_template
            or PromptTemplate(
                name="resume_extract",
                version="v1",
                system_tmpl=DEFAULT_SYSTEM_PROMPT,
                user_tmpl=DEFAULT_USER_TMPL,
            )
        )
        self._log = get_logger(__name__)

    async def parse(self, src: Union[str, Path, bytes]) -> ResumeInfo:
        self._log.info("Парсинг резюме: начинаем извлечение текста")
        text = self._extractor.extract_text(src)
        self._log.info("Текст извлечён, длина=%d", len(text))
        prompt = self._template.render({"resume_text": text})
        self._log.info(
            "Вызов LLM: template=%s/%s", self._template.name, self._template.version
        )
        result = await self._llm.generate_structured(
            prompt=prompt,
            schema=ResumeInfo,
            temperature=0.1,
        )
        self._log.info(
            "Резюме распознано: %s %s", result.first_name or "", result.last_name or ""
        )
        return result
