# --- agent_meta ---
# role: examples-runner
# owner: @backend
# contract: CLI: генерация сопроводительного письма из ResumeInfo и VacancyInfo (онлайн/офлайн)
# last_reviewed: 2025-08-10
# interfaces:
#   - main(resume_pdf: Path | None, vacancy_json: Path, fake_llm: bool) -> int
# --- /agent_meta ---

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any

from src.utils import init_logging_from_env, get_logger
from src.parsing.resume.parser import LLMResumeParser
from src.parsing.llm.client import LLMClient
from src.parsing.vacancy.mapper import map_hh_json_to_vacancy
from src.models.resume_models import ResumeInfo
from src.llm_cover_letter import (
    LLMCoverLetterGenerator,
    CoverLetterOptions,
    EnhancedCoverLetter,
    RoleType,
)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def _load_resume(resume_pdf: Path | None, fake_llm: bool) -> ResumeInfo:
    if fake_llm or resume_pdf is None:
        class _FakeLLMForResume(LLMClient):
            async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):  # type: ignore[override]
                return schema.model_validate(
                    {
                        "first_name": "Иван",
                        "last_name": "Иванов",
                        "middle_name": None,
                        "title": "Software Engineer",
                        "total_experience": 36,
                        "skills": "Python, FastAPI, AsyncIO",
                        "skill_set": ["Python", "FastAPI", "PostgreSQL"],
                        "experience": [
                            {
                                "description": "Разработка бэкенда на FastAPI, рост производительности на 30%",
                                "position": "Backend Engineer",
                                "company": "Acme",
                                "start": "2022-01",
                                "end": "2024-06",
                            }
                        ],
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

        parser = LLMResumeParser(llm=_FakeLLMForResume())
        return await parser.parse(b"dummy")

    if not resume_pdf.exists():
        raise FileNotFoundError(f"Файл резюме не найден: {resume_pdf}")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY не установлен. Используйте --fake-llm или задайте ключ.")
    parser = LLMResumeParser(openai_model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4.1"))
    return await parser.parse(resume_pdf)


async def main_async(resume_pdf: Path | None, vacancy_json: Path, fake_llm: bool, save_result: bool = False) -> int:
    log = get_logger("examples.generate_cover_letter")
    log.info("Старт генерации сопроводительного письма")

    # Резюме
    resume = await _load_resume(resume_pdf, fake_llm)

    # Вакансия
    if not vacancy_json.exists():
        raise FileNotFoundError(f"Файл вакансии не найден: {vacancy_json}")
    vacancy = map_hh_json_to_vacancy(_read_json(vacancy_json))

    # Генератор письма
    if fake_llm:
        class _FakeLLMForLetter(LLMClient):
            async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):  # type: ignore[override]
                return schema.model_validate(
                    {
                        "role_type": "DEVELOPER",
                        "company_context": {
                            "company_name": vacancy.company_name,
                            "company_size": "MEDIUM",
                            "company_culture": None,
                            "product_info": None,
                        },
                        "estimated_length": "MEDIUM",
                        "skills_match": {
                            "matched_skills": ["Python"],
                            "relevant_experience": "3 года бэкенд разработки на FastAPI",
                            "quantified_achievement": "Сократил латентность API на 30%",
                            "growth_potential": None,
                        },
                        "personalization": {
                            "company_hook": f"Интерес к продукту {vacancy.company_name}",
                            "role_motivation": "Хочу развиваться в backend архитектуре",
                            "value_proposition": "Повышу производительность сервисов и улучшу DX команды",
                            "company_knowledge": None,
                        },
                        "subject_line": "Отклик на позицию Backend Engineer",
                        "personalized_greeting": "Здравствуйте!",
                        "opening_hook": "За последний год ускорил API на 30% в Acme",
                        "company_interest": f"Нравится стек и продукт {vacancy.company_name}",
                        "relevant_experience": "Опыт в FastAPI, SQL, очередях",
                        "value_demonstration": "Могу оптимизировать узкие места и добавить мониторинг",
                        "growth_mindset": None,
                        "professional_closing": "Готов обсудить детали на интервью",
                        "signature": "Иван Иванов, email@example.com",
                        "personalization_score": 7,
                        "professional_tone_score": 8,
                        "relevance_score": 7,
                        "improvement_suggestions": ["Добавить портфолио", "Уточнить метрики"]
                    }
                )

        gen = LLMCoverLetterGenerator(llm=_FakeLLMForLetter())
    else:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY не установлен. Используйте --fake-llm или задайте ключ.")
        gen = LLMCoverLetterGenerator()

    letter = await gen.generate(
        resume=resume,
        vacancy=vacancy,
        options=CoverLetterOptions(role_hint=RoleType.DEVELOPER)
    )

    # Сохранение результата в тестовые данные
    if save_result:
        test_data_dir = Path("tests/data")
        test_data_dir.mkdir(exist_ok=True)
        
        random_id = str(uuid.uuid4())[:8]
        result_filename = f"cover_letter_result_{random_id}.json"
        result_path = test_data_dir / result_filename
        
        with result_path.open("w", encoding="utf-8") as f:
            json.dump(letter.model_dump(), f, ensure_ascii=False, indent=2)
        
        print("\n=== RESULT SAVED ===")
        print(f"Saved to: {result_path}")
        print(f"File ID: {random_id}")
        print(f"Use for PDF testing: python examples/test_pdf_export.py --feature cover_letter --result-file {result_filename}")

    print("\n=== EnhancedCoverLetter (JSON) ===")
    print(json.dumps(letter.model_dump(mode="json"), indent=2, ensure_ascii=False))

    print("\n=== Email Text ===")
    print(gen.format_for_email(letter))

    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Генерация сопроводительного письма (онлайн/офлайн)")
    p.add_argument(
        "--resume-pdf",
        type=Path,
        default=None,
        help="Путь к PDF резюме (если не указан, используется фейковое резюме)",
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
        help="Офлайн режим без сетевого вызова LLM",
    )
    p.add_argument(
        "--save-result",
        action="store_true",
        help="Сохранить результат в tests/data для использования в тестах",
    )
    return p


def main() -> int:
    init_logging_from_env()
    args = build_arg_parser().parse_args()
    return asyncio.run(main_async(args.resume_pdf, args.vacancy, args.fake_llm, args.save_result))


if __name__ == "__main__":
    raise SystemExit(main())

