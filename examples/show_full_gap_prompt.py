# examples/show_full_gap_prompt.py
# --- agent_meta ---
# role: gap-analyzer-prompt-demo
# owner: @backend
# contract: Демонстрация полного промпта GAP-анализатора (system + user) на тестовых данных
# last_reviewed: 2025-08-15
# interfaces:
#   - main(): печать сгенерированного промпта для gap_analyzer.v1
# --- /agent_meta ---

from __future__ import annotations

import json
from pathlib import Path

from src.models import ResumeInfo, VacancyInfo
from src.llm_gap_analyzer import LLMGapAnalyzerGenerator, GapAnalyzerOptions


def load_test_data() -> tuple[ResumeInfo, VacancyInfo]:
    data_dir = Path(__file__).parent.parent / "tests" / "data"
    with (data_dir / "simple_resume.json").open("r", encoding="utf-8") as f:
        resume = ResumeInfo(**json.load(f))
    with (data_dir / "simple_vacancy.json").open("r", encoding="utf-8") as f:
        vacancy = VacancyInfo(**json.load(f))
    return resume, vacancy


async def build_prompt_demo(prompt_version: str = "gap_analyzer.v1", include_summary: bool = True):
    print(f"=== GAP Analyzer — Демонстрация полного промпта ({prompt_version}) ===\n")

    resume, vacancy = load_test_data()
    generator = LLMGapAnalyzerGenerator()
    options = GapAnalyzerOptions(
        prompt_version=prompt_version,
        language="ru",
        temperature=0.2,
        include_skill_match_summary=include_summary,
        extra_context={
            "user_notes": "Обратить особое внимание на Python и FastAPI опыт",
            "priority_areas": ["технические навыки", "опыт разработки API"],
            "custom_focus": "Искать метрики производительности в проектах"
        }
    )

    # Собираем промпт через внутреннюю сборку генератора (без вызова LLM)
    merged = generator._merge_with_defaults(options)  # type: ignore[attr-defined]
    prompt = await generator._build_prompt(resume, vacancy, merged)  # type: ignore[attr-defined]

    print("=" * 80)
    print("🎯 SYSTEM PROMPT:")
    print("=" * 80)
    print(prompt.system)
    print()

    print("=" * 80)
    print("🎯 USER PROMPT:")
    print("=" * 80)
    print(prompt.user[:20000] + "..." if len(prompt.user or "") > 20000 else prompt.user)
    print()

    print("📊 СТАТИСТИКА:")
    print(f"System prompt: {len(prompt.system or '')} символов")
    print(f"User prompt: {len(prompt.user or '')} символов")
    print(f"Общий размер: {len((prompt.system or '') + (prompt.user or ''))} символов")


def main():
    import asyncio
    asyncio.run(build_prompt_demo())


if __name__ == "__main__":
    main()

