# src/llm_cover_letter/formatter.py
# --- agent_meta ---
# role: llm-cover-letter-formatter
# owner: @backend
# contract: Форматирование ResumeInfo и VacancyInfo в текстовые блоки для промпта; формат письма для email
# last_reviewed: 2025-08-10
# interfaces:
#   - format_resume_for_cover_letter(resume: ResumeInfo) -> str
#   - format_vacancy_for_cover_letter(vacancy: VacancyInfo) -> str
# --- /agent_meta ---

from __future__ import annotations

from typing import List

from src.models.resume_models import ResumeInfo, Contact
from src.models.vacancy_models import VacancyInfo


def _format_contact(c: Contact) -> str:
    try:
        val = c.value
        if isinstance(val, str):
            v = val
        else:
            v = val.formatted
        return f"- {c.type.name}: {v}"
    except Exception:
        return "- Контакт: (не распознан)"


def format_resume_for_cover_letter(resume: ResumeInfo) -> str:
    parts: List[str] = []
    parts.append("## Профиль кандидата")
    fio = " ".join(filter(None, [resume.last_name or "", resume.first_name or "", resume.middle_name or ""]))
    parts.append(f"**ФИО:** {fio.strip() or 'Не указано'}")
    if resume.total_experience is not None:
        years = resume.total_experience // 12
        months = resume.total_experience % 12
        if years > 0:
            exp = f"{years} лет" + (f" {months} мес." if months else "")
        else:
            exp = f"{months} мес."
        parts.append(f"**Общий опыт работы:** {exp}")
    parts.append("")

    parts.append("### Профессиональная специализация")
    parts.append(f"**Желаемая должность:** {resume.title or 'Не указана'}")
    parts.append("")

    parts.append("### Профессиональные компетенции")
    parts.append(resume.skills or "Не указаны")
    parts.append("")

    parts.append("### Технические навыки и технологии")
    if resume.skill_set:
        parts.extend(f"- {s}" for s in resume.skill_set)
    else:
        parts.append("Не указаны")
    parts.append("")

    parts.append("### Опыт и достижения")
    if resume.experience:
        for i, e in enumerate(resume.experience, 1):
            period = ""
            if e.start or e.end:
                period = f" ({(e.start or '')} - {(e.end or 'по наст.')})"
            parts.append(f"{i}. {e.position} | {e.company or ''}{period}")
            parts.append(e.description)
    else:
        parts.append("Не указан")
    parts.append("")

    if resume.languages:
        parts.append("### Языки")
        parts.extend(f"- {l.name}: {l.level.name}" for l in resume.languages)
        parts.append("")

    if resume.contact:
        parts.append("### Контакты")
        parts.extend(_format_contact(c) for c in resume.contact)
        parts.append("")

    return "\n".join(parts).strip()


def format_vacancy_for_cover_letter(vacancy: VacancyInfo) -> str:
    parts: List[str] = []
    parts.append("## Вакансия")
    parts.append(f"**Позиция:** {vacancy.name}")
    parts.append(f"**Компания:** {vacancy.company_name}")
    parts.append("")

    if vacancy.professional_roles:
        parts.append("### Профессиональные роли")
        parts.extend(f"- {r.name}" for r in vacancy.professional_roles)
        parts.append("")

    parts.append("### Описание")
    parts.append(vacancy.description)
    parts.append("")

    parts.append("### Ключевые навыки")
    if vacancy.key_skills:
        parts.extend(f"- {s}" for s in vacancy.key_skills)
    else:
        parts.append("Не указаны")
    parts.append("")

    if vacancy.experience:
        parts.append("### Требуемый опыт")
        parts.append(f"- id: {vacancy.experience.id}")
        parts.append("")

    return "\n".join(parts).strip()


def format_letter_for_email_text(letter) -> str:
    return (
        f"Тема: {letter.subject_line}\n\n"
        f"{letter.personalized_greeting}\n\n"
        f"{letter.opening_hook}\n\n"
        f"{letter.company_interest}\n\n"
        f"{letter.relevant_experience}\n\n"
        f"{letter.value_demonstration}\n\n"
        f"{(letter.growth_mindset or '').strip()}\n\n"
        f"{letter.professional_closing}\n\n"
        f"{letter.signature}"
    )
