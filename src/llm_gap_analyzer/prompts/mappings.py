# src/llm_gap_analyzer/prompts/mappings.py
# --- agent_meta ---
# role: llm-gap-analyzer-mappings
# owner: @backend
# contract: Динамические блоки промптов для GAP-анализатора
# last_reviewed: 2025-08-15
# interfaces:
#   - build_enum_guidance() -> str
#   - extract_requirements_from_vacancy(vacancy: VacancyInfo) -> str
#   - build_skills_match_summary(resume: ResumeInfo, vacancy: VacancyInfo) -> str
# --- /agent_meta ---

from __future__ import annotations

from typing import List

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_cover_letter.formatter import analyze_skills_match

def extract_requirements_from_vacancy(vacancy: VacancyInfo) -> str:
    """Выделяет требования из вакансии в виде списка для направления LLM."""
    parts: List[str] = []
    parts.append("## Требования вакансии (для анализа)")
    parts.append("")
    
    if vacancy.key_skills:
        parts.append("### Ключевые навыки")
        for s in vacancy.key_skills:
            name = s if isinstance(s, str) else getattr(s, 'name', str(s))
            parts.append(f"- {name}")
        parts.append("")
    
    if vacancy.professional_roles:
        parts.append("### Профессиональные роли")
        for role in vacancy.professional_roles:
            name = getattr(role, 'name', str(role))
            parts.append(f"- {name}")
        parts.append("")
    
    if vacancy.experience and vacancy.experience.id:
        parts.append("### Требуемый опыт")
        parts.append(f"- Идентификатор уровня: {vacancy.experience.id}")
        parts.append("")
    
    return "\n".join(parts).strip()


def build_skills_match_summary(resume: ResumeInfo, vacancy: VacancyInfo) -> str:
    """Короткий свод совпадений/пробелов по навыкам (переиспользуем существующий анализ)."""
    summary = analyze_skills_match(resume, vacancy)
    # Убираем заголовок верхнего уровня, оставляем компактный блок
    return summary.replace("## АНАЛИЗ СООТВЕТСТВИЯ НАВЫКОВ\n\n", "").strip()

