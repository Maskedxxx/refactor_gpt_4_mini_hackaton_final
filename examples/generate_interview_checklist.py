# examples/generate_interview_checklist.py
# --- agent_meta ---
# role: examples-runner
# owner: @backend
# contract: CLI: генерация профессионального чек-листа подготовки к интервью из ResumeInfo и VacancyInfo (онлайн/офлайн)
# last_reviewed: 2025-08-18
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
from src.llm_interview_checklist import (
    LLMInterviewChecklistGenerator,
    InterviewChecklistOptions,
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
                        "first_name": "Алексей",
                        "last_name": "Петров",
                        "middle_name": None,
                        "title": "Senior Python Developer",
                        "total_experience": 60,  # 5 лет
                        "skills": "Python, Django, FastAPI, PostgreSQL, Redis, Docker, Kubernetes",
                        "skill_set": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
                        "experience": [
                            {
                                "description": "Руководство командой из 4 разработчиков, архитектура микросервисов, внедрение CI/CD",
                                "position": "Senior Backend Developer",
                                "company": "TechCorp",
                                "start": "2021-03",
                                "end": "2024-08",
                            },
                            {
                                "description": "Разработка высоконагруженных API, оптимизация производительности БД",
                                "position": "Python Developer",
                                "company": "DataFlow",
                                "start": "2019-01",
                                "end": "2021-02",
                            }
                        ],
                        "employments": [],
                        "schedules": [],
                        "languages": [{"name": "Русский", "level": "native"}, {"name": "Английский", "level": "upper-intermediate"}],
                        "relocation": None,
                        "salary": {"amount": 280000, "currency": "RUR"},
                        "professional_roles": [],
                        "education": {"name": "МГУ", "name_id": None, "organization": "Факультет ВМК", "organization_id": None, "result": "Магистр информатики"},
                        "certificate": [],
                        "contact": [{"type": "email", "value": "alexey.petrov@example.com"}],
                        "site": [{"url": "https://github.com/apetrov"}],
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


async def main_async(
    resume_pdf: Path | None, 
    vacancy_json: Path, 
    fake_llm: bool,
    candidate_level_hint: str | None = None,
    company_format_hint: str | None = None,
    preparation_time: str | None = None,
    save_result: bool = False
) -> int:
    log = get_logger("examples.generate_interview_checklist")
    log.info("Старт генерации чек-листа подготовки к интервью")

    # Резюме
    resume = await _load_resume(resume_pdf, fake_llm)

    # Вакансия
    if not vacancy_json.exists():
        raise FileNotFoundError(f"Файл вакансии не найден: {vacancy_json}")
    vacancy = map_hh_json_to_vacancy(_read_json(vacancy_json))

    # Генератор чек-листа
    if fake_llm:
        class _FakeLLMForChecklist(LLMClient):
            async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):  # type: ignore[override]
                return schema.model_validate(
                    {
                        "position_title": vacancy.name,
                        "company_name": vacancy.company_name,
                        "personalization_context": {
                            "candidate_level": "SENIOR",
                            "vacancy_type": "DEVELOPER", 
                            "company_format": "MEDIUM_COMPANY",
                            "key_gaps_identified": ["Kubernetes", "системный дизайн high-load"],
                            "candidate_strengths": ["Python", "Django", "лидерские навыки"],
                            "critical_focus_areas": ["архитектура", "управление командой"]
                        },
                        "executive_summary": "Кандидат имеет сильный опыт в Python/Django, но нужно усилить знания по системному дизайну и Kubernetes",
                        "preparation_strategy": "Фокус на архитектурных навыках и лидерских компетенциях для Senior позиции",
                        "time_estimates": {
                            "total_time_needed": "20 часов за 2 недели",
                            "critical_tasks_time": "8 часов на техническую подготовку",
                            "important_tasks_time": "6 часов на поведенческие навыки",
                            "optional_tasks_time": "4 часа на исследование компании",
                            "daily_schedule_suggestion": "1-1.5 часа в день в течение 2 недель",
                        },
                        "technical_preparation": [
                            {
                                "category": "профильные_знания",
                                "task_title": "Повторение Python и Django",
                                "description": "Изучить архитектурные паттерны Django, ORM, middleware",
                                "priority": "КРИТИЧНО",
                                "estimated_time": "4 часа",
                                "specific_resources": ["Django Documentation", "Two Scoops of Django"],
                                "success_criteria": "Понимать MVT, умение объяснить жизненный цикл запроса"
                            },
                            {
                                "category": "недостающие_технологии", 
                                "task_title": "Изучение PostgreSQL оптимизации",
                                "description": "Индексы, планы запросов, оптимизация производительности",
                                "priority": "ВАЖНО",
                                "estimated_time": "3 часа",
                                "specific_resources": ["PostgreSQL Performance Tuning"],
                                "success_criteria": "Умение анализировать EXPLAIN ANALYZE"
                            }
                        ],
                        "behavioral_preparation": [
                            {
                                "category": "самопрезентация",
                                "skill_title": "Презентация опыта",
                                "description": "Подготовка краткого рассказа о себе и ключевых достижениях",
                                "priority": "КРИТИЧНО", 
                                "practice_scenarios": ["Tell me about yourself", "Walk me through your resume"],
                                "star_examples": [
                                    {
                                        "situation": "Падение производительности API под нагрузкой",
                                        "task": "Найти и устранить узкие места", 
                                        "action": "Профилирование, оптимизация запросов, внедрение кеширования",
                                        "result": "Улучшение производительности на 40%, уменьшение латентности"
                                    }
                                ],
                                "estimated_prep_time": "2 часа"
                            }
                        ],
                        "company_research": [
                            {
                                "category": "компания_история",
                                "research_title": f"История и миссия {vacancy.company_name}",
                                "description": "Изучить основание, миссию, ценности компании",
                                "priority": "ВАЖНО",
                                "research_steps": ["Посетить сайт компании", "Прочитать About Us", "Изучить миссию и ценности"],
                                "expected_insight": "Понимание культуры и направления развития",
                                "questions_to_ask": ["Как развивается продуктовая стратегия?", "Какие ценности важны для команды?"]
                            }
                        ],
                        "technical_stack_study": [
                            {
                                "technology": "Python",
                                "current_level": "ADVANCED", 
                                "required_level": "ADVANCED",
                                "study_plan": "Повторить async/await, контекстные менеджеры",
                                "practice_tasks": ["Создать async web scraper"],
                                "time_needed": "2 часа"
                            }
                        ],
                        "mock_interviews": [
                            {
                                "session_type": "техническое",
                                "focus_areas": ["системный дизайн", "кодирование"],
                                "estimated_duration": "1 час",
                                "preparation_notes": "Подготовить несколько архитектурных решений",
                                "success_metrics": "Способность объяснить решения и trade-offs"
                            }
                        ],
                        "environment_preparation": [
                            {
                                "category": "техническая_настройка", 
                                "checklist_items": ["Настроить IDE", "Проверить интернет", "Подготовить код examples"],
                                "importance_explanation": "Технические сбои могут испортить впечатление"
                            }
                        ],
                        "additional_actions": [
                            {
                                "category": "профили",
                                "action_title": "Обновить LinkedIn профиль",
                                "description": "Добавить последние достижения и навыки",
                                "urgency": "ВАЖНО",
                                "implementation_steps": ["Обновить experience", "Добавить skills", "Запросить рекомендации"]
                            }
                        ],
                    }
                )

        gen = LLMInterviewChecklistGenerator(llm=_FakeLLMForChecklist())
    else:
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY не установлен. Используйте --fake-llm или задайте ключ.")
        gen = LLMInterviewChecklistGenerator()

    # Настройка опций генерации
    options = InterviewChecklistOptions(
        candidate_level_hint=candidate_level_hint,
        company_format_hint=company_format_hint,
        preparation_time_available=preparation_time or "2 недели",
        focus_areas=["системный дизайн", "лидерство", "Python"] if candidate_level_hint == "SENIOR" else None,
    )

    checklist = await gen.generate(
        resume=resume,
        vacancy=vacancy,
        options=options
    )

    # Сохранение результата в тестовые данные
    if save_result:
        test_data_dir = Path("tests/data")
        test_data_dir.mkdir(exist_ok=True)
        
        random_id = str(uuid.uuid4())[:8]
        result_filename = f"interview_checklist_result_{random_id}.json"
        result_path = test_data_dir / result_filename
        
        with result_path.open("w", encoding="utf-8") as f:
            json.dump(checklist.model_dump(), f, ensure_ascii=False, indent=2)
        
        print("\n=== RESULT SAVED ===")
        print(f"Saved to: {result_path}")
        print(f"File ID: {random_id}")
        print(f"Use for PDF testing: python examples/test_pdf_export.py --feature interview_checklist --result-file {result_filename}")

    print("\n=== ProfessionalInterviewChecklist (JSON) ===")
    print(json.dumps(checklist.model_dump(mode="json"), indent=2, ensure_ascii=False))

    print("\n=== Formatted Checklist Summary ===")
    print(f"📋 Чек-лист подготовки к интервью: {checklist.position_title}")
    print(f"🏢 Компания: {checklist.company_name}")
    print(f"👤 Уровень: {checklist.personalization_context.candidate_level}")
    print(f"🎯 Тип роли: {checklist.personalization_context.vacancy_type}")
    print(f"⏰ Общее время подготовки: {checklist.time_estimates.total_time_needed}")
    
    print("\n🔧 Техническая подготовка:")
    print(f"  Всего задач: {len(checklist.technical_preparation)}")
    if checklist.technical_preparation:
        tech_categories = set(item.category for item in checklist.technical_preparation)
        print(f"  Категории: {', '.join(tech_categories)}")
    
    print("\n💬 Поведенческая подготовка:")
    print(f"  Всего навыков: {len(checklist.behavioral_preparation)}")
    if checklist.behavioral_preparation:
        behavior_categories = set(item.category for item in checklist.behavioral_preparation)
        print(f"  Категории: {', '.join(behavior_categories)}")
    
    print("\n🏢 Исследование компании:")
    print(f"  Всего направлений: {len(checklist.company_research)}")
    
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Генерация чек-листа подготовки к интервью (онлайн/офлайн)")
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
        "--candidate-level",
        choices=["JUNIOR", "MIDDLE", "SENIOR", "LEAD"],
        help="Подсказка об уровне кандидата",
    )
    p.add_argument(
        "--company-format",
        choices=["STARTUP", "MEDIUM_COMPANY", "LARGE_CORP", "INTERNATIONAL"],
        help="Подсказка о формате компании",
    )
    p.add_argument(
        "--preparation-time",
        default="2 недели",
        help="Доступное время для подготовки (по умолчанию: 2 недели)",
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
    return asyncio.run(main_async(
        args.resume_pdf, 
        args.vacancy, 
        args.fake_llm,
        args.candidate_level,
        args.company_format,
        args.preparation_time,
        args.save_result
    ))


if __name__ == "__main__":
    raise SystemExit(main())