# examples/generate_gap_analysis.py
# --- agent_meta ---
# role: gap-analyzer-cli
# owner: @backend
# contract: CLI: генерация GAP-анализа из ResumeInfo и VacancyInfo (онлайн/офлайн)
# last_reviewed: 2025-08-15
# interfaces:
#   - main(resume_json: Path, vacancy_json: Path, fake_llm: bool) -> int
# --- /agent_meta ---

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any

from src.utils import get_logger
from src.parsing.llm.client import LLMClient
from src.models import ResumeInfo, VacancyInfo
from src.llm_gap_analyzer import LLMGapAnalyzerGenerator, GapAnalyzerOptions
from src.llm_gap_analyzer.config import GapAnalyzerSettings
from src.llm_gap_analyzer.models import EnhancedResumeTailoringAnalysis


log = get_logger("examples.generate_gap_analysis")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class _FakeLLMForGap(LLMClient):
    async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):  # type: ignore[override]
        # Возвращаем простой валидный каркас ответа
        return schema.model_validate(
            {
                "primary_screening": {
                    "job_title_match": True,
                    "experience_years_match": True,
                    "key_skills_visible": True,
                    "location_suitable": True,
                    "salary_expectations_match": True,
                    "overall_screening_result": "ПРИНЯТЬ",
                    "screening_notes": "Быстрое совпадение по ключевым признакам",
                },
                "requirements_analysis": [
                    {
                        "requirement_text": "Python, FastAPI",
                        "requirement_type": "MUST_HAVE",
                        "skill_category": "HARD_SKILLS",
                        "compliance_status": "FULL_MATCH",
                        "evidence_in_resume": "Опыт 3 года с FastAPI",
                        "gap_description": None,
                        "impact_on_decision": "Подтверждает релевантность кандидата",
                    }
                ],
                "quality_assessment": {
                    "structure_clarity": 8,
                    "content_relevance": 8,
                    "achievement_focus": 7,
                    "adaptation_quality": 7,
                    "overall_impression": "СИЛЬНЫЙ",
                    "quality_notes": "Хорошая структура, есть конкретные достижения",
                },
                "critical_recommendations": [],
                "important_recommendations": [
                    {
                        "section": "навыки",
                        "criticality": "IMPORTANT",
                        "issue_description": "Добавить метрики влияния",
                        "specific_actions": ["Указать рост производительности и цифры"],
                        "example_wording": "Сократил время ответа API на 30%",
                        "business_rationale": "Метрики повышают доверие к опыту",
                    }
                ],
                "optional_recommendations": [],
                "overall_match_percentage": 82,
                "hiring_recommendation": "ДА",
                "key_strengths": ["Сильный бэкенд", "Опыт FastAPI"],
                "major_gaps": ["Недостаточно ML-опыта"],
                "next_steps": "Интервью с техническим лидом",
            }
        )


async def run_async(resume_json: Path, vacancy_json: Path, *, fake_llm: bool, prompt_version: str, save_result: bool = False) -> int:
    resume = ResumeInfo(**_read_json(resume_json))
    vacancy = VacancyInfo(**_read_json(vacancy_json))

    llm = _FakeLLMForGap() if fake_llm else None
    # Поддержка пер-фичної модели через GAP_ANALYZER_MODEL_NAME
    settings = GapAnalyzerSettings()
    gen = LLMGapAnalyzerGenerator(
        llm=llm,
        openai_model_name=settings.model_name,
    )

    if not fake_llm and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY не установлен. Используйте --fake-llm или задайте ключ.")

    options = GapAnalyzerOptions(
        prompt_version=prompt_version,
        temperature=0.2,
        language="ru",
        extra_context={
            "user_notes": "Обратить особое внимание на Python и FastAPI опыт",
            "priority_areas": ["технические навыки", "опыт разработки API"],
            "custom_focus": "Искать метрики производительности в проектах"
        }
    )

    log.info("Запуск GAP-анализа: version=%s, fake_llm=%s", prompt_version, fake_llm)
    result: EnhancedResumeTailoringAnalysis = await gen.generate(resume, vacancy, options)

    # Печатаем компактный свод и полный JSON
    print("\n=== GAP ANALYSIS SUMMARY ===")
    print(f"Match: {result.overall_match_percentage}% | Hiring: {result.hiring_recommendation}")
    if result.requirements_analysis:
        first = result.requirements_analysis[0]
        print(f"1st requirement: '{first.requirement_text}' → {first.compliance_status}")
    
    # Сохранение результата в тестовые данные
    if save_result:
        test_data_dir = Path("tests/data")
        test_data_dir.mkdir(exist_ok=True)
        
        random_id = str(uuid.uuid4())[:8]
        result_filename = f"gap_analysis_result_{random_id}.json"
        result_path = test_data_dir / result_filename
        
        with result_path.open("w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)
        
        print("\n=== RESULT SAVED ===")
        print(f"Saved to: {result_path}")
        print(f"File ID: {random_id}")
        print(f"Use for PDF testing: python -m tests.test_pdf_export --result-file {result_filename}")
    
    print("\n=== FULL RESULT (JSON) ===")
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))

    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="GAP-анализ резюме относительно вакансии")
    p.add_argument("--resume", type=Path, default=Path("tests/data/simple_resume.json"), help="Путь к JSON резюме")
    p.add_argument("--vacancy", type=Path, default=Path("tests/data/simple_vacancy.json"), help="Путь к JSON вакансии")
    p.add_argument("--prompt-version", type=str, default="gap_analyzer.v1", help="Версия промпта")
    p.add_argument("--fake-llm", action="store_true", help="Использовать фейковый LLM (офлайн)")
    p.add_argument("--save-result", action="store_true", help="Сохранить результат в tests/data для использования в тестах")
    args = p.parse_args()

    return asyncio.run(run_async(
        args.resume, 
        args.vacancy, 
        fake_llm=args.fake_llm, 
        prompt_version=args.prompt_version,
        save_result=args.save_result
    ))


if __name__ == "__main__":
    raise SystemExit(main())
