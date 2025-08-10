# examples/parse_parsers.py
# --- agent_meta ---
# role: examples-runner
# owner: @backend
# contract: CLI-скрипт для демонстрации парсинга резюме (PDF+LLM) и вакансии (локальный HH JSON)
# last_reviewed: 2025-08-10
# interfaces:
#   - main(resume_pdf: Path, vacancy_json: Path, use_fake_llm: bool) -> None
#   - Запуск: python examples/parse_parsers.py --resume tests/data/resume.pdf --vacancy tests/data/vacancy.json
# --- /agent_meta ---

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

from src.utils import init_logging_from_env, get_logger
from src.parsing.resume.parser import LLMResumeParser
from src.parsing.vacancy.mapper import map_hh_json_to_vacancy
from src.models.resume_models import ResumeInfo


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def _run_resume_parse(resume_pdf: Path, use_fake_llm: bool) -> ResumeInfo:
    """Парсит резюме из PDF. При use_fake_llm=True выполнит запуск без сетевого вызова.

    Для реального вызова требуется переменная окружения OPENAI_API_KEY и (опц.) OPENAI_MODEL_NAME.
    """
    log = get_logger(__name__)
    if not resume_pdf.exists():
        raise FileNotFoundError(f"Файл резюме не найден: {resume_pdf}")

    if use_fake_llm:
        # Локальная заглушка для офлайн-сред
        from src.parsing.llm.client import LLMClient

        class _FakeLLM(LLMClient):
            async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):  # type: ignore[override]
                # Возвращаем минимально валидную структуру
                return schema.model_validate(
                    {
                        "first_name": None,
                        "last_name": None,
                        "middle_name": None,
                        "title": "Software Engineer",
                        "total_experience": 0,
                        "skills": "",
                        "skill_set": [],
                        "experience": [],
                        "employments": [],
                        "schedules": [],
                        "languages": [],
                        "relocation": None,
                        "salary": None,
                        "professional_roles": [],
                        "education": None,
                        "certificate": [],
                        "contact": [],
                        "site": [],
                    }
                )

        log.info("Используется фейковый LLM для парсинга резюме (офлайн)")
        parser = LLMResumeParser(llm=_FakeLLM())
    else:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY не установлен. Установите токен или запустите с --fake-llm."
            )
        parser = LLMResumeParser(
            openai_model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4.1")
        )

    return await parser.parse(resume_pdf)


async def _run_vacancy_parse(vacancy_json: Path):
    """Парсит вакансию из локального JSON, используя маппер в VacancyInfo."""
    if not vacancy_json.exists():
        raise FileNotFoundError(f"Файл вакансии не найден: {vacancy_json}")
    data = _read_json(vacancy_json)
    return map_hh_json_to_vacancy(data)


async def main_async(resume_pdf: Path, vacancy_json: Path, use_fake_llm: bool) -> int:
    log = get_logger("examples.parse_parsers")
    log.info("Старт демо-парсинга. Резюме=%s, Вакансия=%s", resume_pdf, vacancy_json)

    # Резюме из PDF через LLM
    resume = await _run_resume_parse(resume_pdf, use_fake_llm)
    print("\n=== ResumeInfo ===")
    print(json.dumps(resume.model_dump(mode="json"), indent=2, ensure_ascii=False))

    # Вакансия из локального JSON
    vacancy = await _run_vacancy_parse(vacancy_json)
    print("\n=== VacancyInfo ===")
    print(json.dumps(vacancy.model_dump(mode="json"), indent=2, ensure_ascii=False))

    log.info("Демо-парсинг завершён успешно")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Демонстрация: парсинг резюме (PDF -> LLM -> ResumeInfo) и вакансии (локальный HH JSON -> VacancyInfo)"
        )
    )
    p.add_argument(
        "--resume",
        type=Path,
        default=Path("tests/data/resume.pdf"),
        help="Путь к PDF с резюме (по умолчанию tests/data/resume.pdf)",
    )
    p.add_argument(
        "--vacancy",
        type=Path,
        default=Path("tests/data/vacancy.json"),
        help="Путь к JSON вакансии (по умолчанию tests/data/vacancy.json)",
    )
    p.add_argument(
        "--fake-llm",
        action="store_true",
        help="Не вызывать внешний LLM, использовать локальную заглушку (офлайн)",
    )
    return p


def main() -> int:
    init_logging_from_env()
    args = build_arg_parser().parse_args()
    return asyncio.run(main_async(args.resume, args.vacancy, args.fake_llm))


if __name__ == "__main__":
    raise SystemExit(main())
