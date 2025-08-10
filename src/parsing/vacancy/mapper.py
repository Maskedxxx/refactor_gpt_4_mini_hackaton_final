# src/parsing/vacancy/mapper.py
# --- agent_meta ---
# role: vacancy-mapper
# owner: @backend
# contract: Преобразование HH JSON вакансии в Pydantic модель VacancyInfo
# last_reviewed: 2025-08-10
# interfaces:
#   - map_hh_json_to_vacancy(data: Dict[str, Any]) -> VacancyInfo
# --- /agent_meta ---

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from src.models.vacancy_models import (
    VacancyInfo,
    EmploymentForm,
    ExperienceVac,
    Schedule,
    Employment,
    ProfessionalRole,
)
from src.utils import get_logger

_log = get_logger(__name__)


def _strip_html(text: Optional[str]) -> str:
    if not text:
        return ""
    return re.sub(r"<.*?>", "", text).strip()


def _extract_roles(data: Dict[str, Any]) -> List[ProfessionalRole]:
    roles = []
    for role in data.get("professional_roles", []) or []:
        if isinstance(role, dict):
            roles.append(ProfessionalRole(name=role.get("name", "")))
    return roles


def map_hh_json_to_vacancy(data: Dict[str, Any]) -> VacancyInfo:
    """Маппинг JSON HH вакансии в доменную модель.

    Нормализуем строки, вытаскиваем вложенные объекты и списки.
    HTML в description очищаем.
    """
    employment_form = None
    if isinstance(data.get("employment_form"), dict):
        employment_form = EmploymentForm(id=data["employment_form"].get("id", ""))

    experience = None
    if isinstance(data.get("experience"), dict):
        experience = ExperienceVac(id=data["experience"].get("id", ""))

    schedule = None
    if isinstance(data.get("schedule"), dict):
        schedule = Schedule(id=data["schedule"].get("id", ""))

    employment = None
    if isinstance(data.get("employment"), dict):
        employment = Employment(id=data["employment"].get("id", ""))

    key_skills = [
        s.get("name", "") for s in (data.get("key_skills", []) or []) if isinstance(s, dict)
    ]

    model = VacancyInfo(
        name=data.get("name", ""),
        company_name=(data.get("employer", {}) or {}).get("name", "Компания"),
        description=_strip_html(data.get("description", "")),
        key_skills=key_skills,
        professional_roles=_extract_roles(data),
        employment_form=employment_form,
        experience=experience,
        schedule=schedule,
        employment=employment,
    )
    _log.info("Vacancy mapped: %s (%s)", model.name, model.company_name)
    return model
