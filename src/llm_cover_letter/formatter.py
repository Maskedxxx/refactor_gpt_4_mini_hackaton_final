# src/llm_cover_letter/formatter.py
# --- agent_meta ---
# role: llm-cover-letter-formatter
# owner: @backend
# contract: Форматирование ResumeInfo и VacancyInfo в текстовые блоки для промпта; анализ соответствия навыков; формат письма для email
# last_reviewed: 2025-08-15
# interfaces:
#   - format_resume_for_cover_letter(resume: ResumeInfo) -> str
#   - format_vacancy_for_cover_letter(vacancy: VacancyInfo) -> str
#   - analyze_skills_match(resume: ResumeInfo, vacancy: VacancyInfo) -> str
#   - analyze_candidate_positioning(resume: ResumeInfo, vacancy: VacancyInfo) -> str
#   - format_cover_letter_context(resume: ResumeInfo, vacancy: VacancyInfo) -> str
#   - format_letter_for_email_text(letter) -> str
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
    """
    Форматирует данные резюме для создания персонализированного сопроводительного письма.
    Фокус на персонализации и создании убедительного контента.
    """
    parts: List[str] = []
    parts.append("## ПРОФИЛЬ КАНДИДАТА")
    parts.append("")
    
    # Персональная информация для обращения
    parts.append("### Личная информация")
    fio = " ".join(filter(None, [resume.last_name or "", resume.first_name or "", resume.middle_name or ""]))
    parts.append(f"**ФИО:** {fio.strip() or 'Не указано'}")
    
    # Общий опыт работы (важно для позиционирования)
    if resume.total_experience is not None:
        years = resume.total_experience // 12
        months = resume.total_experience % 12
        if years > 0:
            exp_text = f"{years} лет {months} мес." if months > 0 else f"{years} лет"
        else:
            exp_text = f"{months} мес."
        parts.append(f"**Общий опыт работы:** {exp_text}")
    else:
        parts.append("**Общий опыт работы:** Не указан")
    parts.append("")

    # Специализация и желаемая позиция
    parts.append("### Профессиональная специализация")
    parts.append(f"**Желаемая должность:** {resume.title or 'Не указана'}")
    parts.append("")

    # Профессиональные навыки и описание
    parts.append("### Профессиональные компетенции")
    parts.append("**Профессиональное описание:**")
    parts.append(resume.skills or "Не указаны")
    parts.append("")

    # Ключевые технические навыки
    parts.append("### Технические навыки и технологии")
    if resume.skill_set:
        for skill in resume.skill_set:
            parts.append(f"- {skill}")
    else:
        parts.append("Не указаны")
    parts.append("")

    # Профессиональный опыт (с акцентом на достижения и компании)
    parts.append("### Карьерная история и ключевые достижения")
    if resume.experience:
        for i, exp in enumerate(resume.experience, 1):
            company = exp.company or 'Компания не указана'
            position = exp.position or 'Должность не указана'
            start = exp.start or ''
            end = exp.end or 'по настоящее время'
            description = exp.description or 'Описание отсутствует'
            
            # Форматируем период работы
            period = f"{start} - {end}" if start else end
            
            parts.append(f"**{i}. {position}** | *{company}*")
            parts.append(f"Период: {period}")
            parts.append("Ключевые достижения и обязанности:")
            parts.append(description)
            parts.append("")
    else:
        parts.append("Карьерная история не указана")
        parts.append("")

    # Сертификаты и дополнительная квалификация
    if hasattr(resume, 'certificate') and resume.certificate:
        parts.append("### Сертификаты и дополнительная квалификация")
        for cert in resume.certificate:
            title = cert.get('title', 'Название сертификата не указано') if isinstance(cert, dict) else str(cert)
            url = cert.get('url') if isinstance(cert, dict) else None
            
            if url:
                parts.append(f"- **{title}** (подтверждение: {url})")
            else:
                parts.append(f"- **{title}**")
        parts.append("")

    # Знание языков (может быть критично для позиции)
    if resume.languages:
        parts.append("### Языковые компетенции")
        for lang in resume.languages:
            parts.append(f"- **{lang.name}:** {lang.level.name}")
        parts.append("")
        
    # Контактная информация (для подписи в письме)
    if resume.contact:
        parts.append("### Контактная информация")
        for contact in resume.contact:
            parts.append(_format_contact(contact))
        parts.append("")

    return "\n".join(parts).strip()


def format_vacancy_for_cover_letter(vacancy: VacancyInfo) -> str:
    """
    Форматирует данные вакансии для создания персонализированного сопроводительного письма.
    Фокус на требованиях и ожиданиях работодателя.
    """
    parts: List[str] = []
    parts.append("## ЦЕЛЕВАЯ ПОЗИЦИЯ И ТРЕБОВАНИЯ")
    parts.append("")
    
    # Название позиции (критично для персонализации)
    parts.append("### Информация о позиции")
    parts.append(f"**Название позиции:** {vacancy.name}")
    parts.append(f"**Компания:** {vacancy.company_name}")
    parts.append("")

    # Профессиональные роли (ожидания работодателя)
    if vacancy.professional_roles:
        parts.append("### Требуемые профессиональные роли")
        for role in vacancy.professional_roles:
            role_name = role.name if hasattr(role, 'name') else str(role)
            parts.append(f"- {role_name}")
        parts.append("")

    # Описание вакансии и задач
    parts.append("### Описание позиции и ключевые задачи")
    parts.append(vacancy.description or "Не указано")
    parts.append("")

    # Требуемые навыки (для демонстрации соответствия)
    parts.append("### Требуемые навыки и технологии")
    if vacancy.key_skills:
        for skill in vacancy.key_skills:
            skill_name = skill if isinstance(skill, str) else skill.get('name', '') if hasattr(skill, 'get') else str(skill)
            parts.append(f"- {skill_name}")
    else:
        parts.append("Не указаны")
    parts.append("")

    # Требуемый опыт работы (влияет на позиционирование кандидата)
    if vacancy.experience and vacancy.experience.id:
        parts.append("### Требования к опыту работы")
        
        exp_mapping = {
            'noExperience': 'Без опыта работы',
            'between1And3': 'От 1 года до 3 лет опыта',
            'between3And6': 'От 3 до 6 лет опыта',
            'moreThan6': 'Более 6 лет опыта'
        }
        
        exp_id = vacancy.experience.id
        exp_text = exp_mapping.get(exp_id, f"Требование: {exp_id}")
        parts.append(f"**Минимальный опыт:** {exp_text}")
        parts.append("")

    return "\n".join(parts).strip()


def analyze_skills_match(resume: ResumeInfo, vacancy: VacancyInfo) -> str:
    """
    Анализирует соответствие навыков кандидата требованиям вакансии.
    """
    parts: List[str] = []
    parts.append("## АНАЛИЗ СООТВЕТСТВИЯ НАВЫКОВ")
    parts.append("")
    
    # Получаем навыки из резюме и вакансии
    resume_skills = set(skill.lower() for skill in (resume.skill_set or []))
    vacancy_skills = set(skill.lower() for skill in (vacancy.key_skills or []))
    matching_skills = resume_skills & vacancy_skills
    
    parts.append("### Соответствие навыков")
    if matching_skills:
        parts.append(f"**Совпадающие навыки ({len(matching_skills)}):**")
        for skill in sorted(matching_skills):
            parts.append(f"- {skill.title()}")
    else:
        parts.append("Прямых совпадений навыков не найдено")
    
    missing_skills = vacancy_skills - resume_skills
    if missing_skills:
        parts.append(f"\n**Навыки вакансии, отсутствующие в резюме ({len(missing_skills)}):**")
        for skill in sorted(list(missing_skills)[:5]):  # Показываем первые 5
            parts.append(f"- {skill.title()}")
        if len(missing_skills) > 5:
            parts.append(f"... и еще {len(missing_skills) - 5}")
    
    parts.append("")
    return "\n".join(parts)


def analyze_candidate_positioning(resume: ResumeInfo, vacancy: VacancyInfo) -> str:
    """
    Определяет уровень позиционирования кандидата относительно требований вакансии.
    """
    parts: List[str] = []
    parts.append("## ПОЗИЦИОНИРОВАНИЕ КАНДИДАТА")
    parts.append("")
    
    # Анализ уровня по опыту
    parts.append("### Уровень по опыту")
    
    total_exp = resume.total_experience or 0
    years_exp = total_exp // 12
    
    if years_exp == 0:
        level = "Junior / Начинающий специалист"
    elif years_exp <= 2:
        level = "Junior+ / Младший специалист"
    elif years_exp <= 5:
        level = "Middle / Средний специалист"
    elif years_exp <= 10:
        level = "Senior / Старший специалист"
    else:
        level = "Lead / Ведущий специалист"
    
    parts.append(f"**Уровень кандидата по опыту:** {level}")
    
    # Анализ требований вакансии
    if vacancy.experience and vacancy.experience.id:
        exp_mapping = {
            'noExperience': 'Junior позиция',
            'between1And3': 'Junior/Middle позиция', 
            'between3And6': 'Middle позиция',
            'moreThan6': 'Senior+ позиция'
        }
        required_exp = vacancy.experience.id
        parts.append(f"**Уровень вакансии:** {exp_mapping.get(required_exp, required_exp)}")
    
    parts.append("")
    return "\n".join(parts)


def format_cover_letter_context(resume: ResumeInfo, vacancy: VacancyInfo) -> str:
    """
    Создает контекстную информацию для более персонализированного письма.
    Объединяет анализ навыков и позиционирования.
    """
    parts: List[str] = []
    parts.append("## КОНТЕКСТ ДЛЯ ПЕРСОНАЛИЗАЦИИ")
    parts.append("")
    
    # Добавляем анализ навыков
    skills_analysis = analyze_skills_match(resume, vacancy)
    parts.append(skills_analysis.replace("## АНАЛИЗ СООТВЕТСТВИЯ НАВЫКОВ\n\n", ""))
    
    # Добавляем позиционирование
    positioning_analysis = analyze_candidate_positioning(resume, vacancy)
    parts.append(positioning_analysis.replace("## ПОЗИЦИОНИРОВАНИЕ КАНДИДАТА\n\n", ""))
    
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
