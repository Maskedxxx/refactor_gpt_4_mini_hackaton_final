# src/llm_gap_analyzer/formatter.py
# --- agent_meta ---
# role: llm-gap-analyzer-formatter
# owner: @backend
# contract: Форматирование резюме и вакансии в markdown-блоки для GAP-анализа
# last_reviewed: 2025-08-15
# interfaces:
#   - format_resume_data(resume_data: dict) -> str
#   - format_vacancy_data(vacancy_data: dict) -> str
# --- /agent_meta ---

"""
Модуль для форматирования данных резюме и вакансии перед отправкой в LLM.
"""

def format_resume_data(resume_data: dict) -> str:
    """
    Форматирует данные резюме в читаемый markdown формат.
    
    Args:
        resume_data: Словарь с данными резюме
        
    Returns:
        str: Форматированный markdown текст резюме
    """
    formatted_text = "# РЕЗЮМЕ КАНДИДАТА\n\n"
    
    # Персональная информация
    formatted_text += "## Персональная информация\n"
    first_name = resume_data.get('first_name', '')
    last_name = resume_data.get('last_name', '')
    middle_name = resume_data.get('middle_name', '')
    
    if first_name or last_name or middle_name:
        full_name = f"{last_name} {first_name} {middle_name}".strip()
        formatted_text += f"ФИО: {full_name}\n"
    else:
        formatted_text += "ФИО: Не указано\n"
    
    # Общий опыт работы
    total_experience = resume_data.get('total_experience')
    if total_experience:
        years = total_experience // 12
        months = total_experience % 12
        exp_text = f"{years} лет {months} мес." if years > 0 else f"{months} мес."
        formatted_text += f"**Общий опыт работы:** {exp_text}\n"
    else:
        formatted_text += "**Общий опыт работы:** Не указан\n"
    
    formatted_text += "\n"
    
    # Основная информация
    formatted_text += "## Желаемая должность\n"
    formatted_text += f"{resume_data.get('title', 'Не указана')}\n\n"
    
    # Навыки и компетенции
    formatted_text += "## Описание навыков\n"
    formatted_text += f"{resume_data.get('skills', 'Не указаны')}\n\n"
    
    # Ключевые навыки
    formatted_text += "## Ключевые навыки\n"
    skill_set = resume_data.get('skill_set', [])
    if skill_set:
        for skill in skill_set:
            formatted_text += f"- {skill}\n"
    else:
        formatted_text += "Не указаны\n"
    formatted_text += "\n"
    
    # Опыт работы (обновлен с учетом company)
    formatted_text += "## Опыт работы\n"
    experience_list = resume_data.get('experience', [])
    if experience_list:
        for i, exp in enumerate(experience_list, 1):
            position = exp.get('position', 'Должность не указана')
            company = exp.get('company', 'Компания не указана')
            start = exp.get('start', 'Дата не указана')
            end = exp.get('end', 'по настоящее время')
            description = exp.get('description', 'Описание отсутствует')
            
            formatted_text += f"### Опыт работы #{i}: {position}\n"
            formatted_text += f"**Компания:** {company}\n"
            formatted_text += f"**Период:** {start} - {end}\n"
            formatted_text += f"**Описание:**\n {description}\n\n"
    else:
        formatted_text += "Опыт работы не указан\n\n"
    
    # Образование
    education = resume_data.get('education')
    if education:
        formatted_text += "## Образование\n"
        
        # Уровень образования
        level = education.get('level')
        if level and level.get('name'):
            formatted_text += f"**Уровень:** {level.get('name')}\n\n"
        
        # Основное образование
        primary = education.get('primary', [])
        if primary:
            formatted_text += "### Основное образование\n"
            for edu in primary:
                name = edu.get('name', 'Учебное заведение не указано')
                organization = edu.get('organization', '')
                result = edu.get('result', '')
                year = edu.get('year', '')
                
                formatted_text += f"**{name}**"
                if year:
                    formatted_text += f" ({year})"
                formatted_text += "\n"
                
                if organization:
                    formatted_text += f"- Факультет/Организация: {organization}\n"
                if result:
                    formatted_text += f"- Специальность: {result}\n"
                formatted_text += "\n"
        
        # Дополнительное образование
        additional = education.get('additional', [])
        if additional:
            formatted_text += "### Дополнительное образование и сертификаты\n"
            for edu in additional:
                name = edu.get('name', 'Курс не указан')
                organization = edu.get('organization', '')
                result = edu.get('result', '')
                year = edu.get('year', '')
                
                formatted_text += f"**{name}**"
                if year:
                    formatted_text += f" ({year})"
                formatted_text += "\n"
                
                if organization:
                    formatted_text += f"- Организация: {organization}\n"
                if result:
                    formatted_text += f"- Результат: {result}\n"
                formatted_text += "\n"
    
    # Сертификаты (новый блок)
    certificates = resume_data.get('certificate', [])
    if certificates:
        formatted_text += "## Сертификаты\n"
        for cert in certificates:
            title = cert.get('title', 'Название сертификата не указано')
            url = cert.get('url')
            
            if url:
                formatted_text += f"- **{title}** ([ссылка]({url}))\n"
            else:
                formatted_text += f"- **{title}**\n"
        formatted_text += "\n"
    
    # Профессиональные роли
    formatted_text += "## Профессиональные роли\n"
    roles = resume_data.get('professional_roles', [])
    if roles:
        for role in roles:
            formatted_text += f"- {role.get('name', '')}\n"
    else:
        formatted_text += "Не указаны\n"
    formatted_text += "\n"
    
    # Контактная информация (новый блок)
    contacts = resume_data.get('contact', [])
    if contacts:
        formatted_text += "## Контактная информация\n"
        for contact in contacts:
            contact_type = contact.get('type', {}).get('name', 'Тип не указан')
            value = contact.get('value')
            
            # Обрабатываем разные типы значений
            if isinstance(value, dict):
                contact_value = value.get('formatted', 'Значение не указано')
            elif isinstance(value, str):
                contact_value = value
            else:
                contact_value = 'Значение не указано'
            
            formatted_text += f"- **{contact_type}:** {contact_value}\n"
        formatted_text += "\n"
    
    # Сайты (новый блок)
    sites = resume_data.get('site', [])
    if sites:
        formatted_text += "## Сайты и профили\n"
        for site in sites:
            site_type = site.get('type', {}).get('name', 'Тип не указан')
            url = site.get('url', 'URL не указан')
            
            formatted_text += f"- **{site_type}:** {url}\n"
        formatted_text += "\n"
    
    # Дополнительная информация
    formatted_text += "## Предпочитаемые типы занятости\n"
    employments = resume_data.get('employments', [])
    if employments:
        for employment in employments:
            formatted_text += f"- {employment}\n"
    else:
        formatted_text += "Не указаны\n"
    formatted_text += "\n"
    
    formatted_text += "## Предпочитаемый график работы\n"
    schedules = resume_data.get('schedules', [])
    if schedules:
        for schedule in schedules:
            formatted_text += f"- {schedule}\n"
    else:
        formatted_text += "Не указан\n"
    formatted_text += "\n"
    
    # Языки
    formatted_text += "## Знание языков\n"
    languages = resume_data.get('languages', [])
    if languages:
        for lang in languages:
            name = lang.get('name', '')
            level = lang.get('level', {}).get('name', '')
            formatted_text += f"- {name}: {level}\n"
    else:
        formatted_text += "Не указаны\n"
    formatted_text += "\n"
    
    # Зарплатные ожидания
    salary = resume_data.get('salary', {})
    if salary and salary.get('amount'):
        formatted_text += f"## Зарплатные ожидания\n{salary.get('amount')} руб.\n\n"
    
    return formatted_text


def format_vacancy_data(vacancy_data: dict) -> str:
    """
    Форматирует данные вакансии в читаемый markdown формат.
    
    Args:
        vacancy_data: Словарь с данными вакансии
        
    Returns:
        str: Форматированный markdown текст вакансии
    """
    formatted_text = "# ОПИСАНИЕ ВАКАНСИИ\n\n"
    
    # Название вакансии (новое поле)
    formatted_text += "## Название вакансии\n"
    formatted_text += f"{vacancy_data.get('name', 'Не указано')}\n\n"
    
    # Описание вакансии
    formatted_text += "## Описание вакансии\n"
    formatted_text += f"{vacancy_data.get('description', 'Не указано')}\n\n"
    
    # Ключевые навыки
    formatted_text += "## Ключевые навыки (требуемые)\n"
    key_skills = vacancy_data.get('key_skills', [])
    if key_skills:
        for skill in key_skills:
            formatted_text += f"- {skill}\n"
    else:
        formatted_text += "Не указаны\n"
    formatted_text += "\n"
    
    # Профессиональные роли (новый блок)
    professional_roles = vacancy_data.get('professional_roles', [])
    if professional_roles:
        formatted_text += "## Требуемые профессиональные роли\n"
        for role in professional_roles:
            formatted_text += f"- {role.get('name', '')}\n"
        formatted_text += "\n"
    
    # Требуемый опыт
    experience = vacancy_data.get('experience', {})
    if experience and experience.get('id'):
        exp_id = experience.get('id')
        exp_text = ""
        
        if exp_id == 'noExperience':
            exp_text = "Без опыта"
        elif exp_id == 'between1And3':
            exp_text = "От 1 года до 3 лет"
        elif exp_id == 'between3And6':
            exp_text = "От 3 до 6 лет"
        elif exp_id == 'moreThan6':
            exp_text = "Более 6 лет"
        else:
            exp_text = exp_id
            
        formatted_text += f"## Требуемый опыт работы\n{exp_text}\n\n"
    
    # Тип занятости
    employment = vacancy_data.get('employment', {})
    if employment and employment.get('id'):
        emp_id = employment.get('id')
        emp_text = ""
        
        if emp_id == 'full':
            emp_text = "Полная занятость"
        elif emp_id == 'part':
            emp_text = "Частичная занятость"
        elif emp_id == 'project':
            emp_text = "Проектная работа"
        elif emp_id == 'volunteer':
            emp_text = "Волонтерство"
        elif emp_id == 'probation':
            emp_text = "Стажировка"
        else:
            emp_text = emp_id
            
        formatted_text += f"## Тип занятости\n{emp_text}\n\n"
    
    # График работы
    schedule = vacancy_data.get('schedule', {})
    if schedule and schedule.get('id'):
        sch_id = schedule.get('id')
        sch_text = ""
        
        if sch_id == 'fullDay':
            sch_text = "Полный день"
        elif sch_id == 'shift':
            sch_text = "Сменный график"
        elif sch_id == 'flexible':
            sch_text = "Гибкий график"
        elif sch_id == 'remote':
            sch_text = "Удаленная работа"
        elif sch_id == 'flyInFlyOut':
            sch_text = "Вахтовый метод"
        else:
            sch_text = sch_id
            
        formatted_text += f"## График работы\n{sch_text}\n\n"
    
    return formatted_text

