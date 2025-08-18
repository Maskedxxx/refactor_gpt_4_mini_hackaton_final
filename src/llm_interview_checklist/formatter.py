# src/llm_interview_checklist/formatter.py
# --- agent_meta ---
# role: llm-interview-checklist-formatter
# owner: @backend
# contract: Форматирование данных резюме и вакансии для генерации чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - format_resume_for_interview_prep()
#   - format_vacancy_for_interview_prep()
# --- /agent_meta ---

from typing import Dict, Any


def format_resume_for_interview_prep(resume_data: Dict[str, Any]) -> str:
    """
    Форматирует данные резюме для анализа текущих компетенций кандидата.
    Объединяет базовый и детальный анализ для полной картины.
    
    Args:
        resume_data: Словарь с данными резюме
        
    Returns:
        str: Форматированный текст резюме для анализа
    """
    formatted_text = "## ПОЛНЫЙ АНАЛИЗ КОМПЕТЕНЦИЙ КАНДИДАТА\n\n"
    
    # Персональная информация и контекст
    formatted_text += "### Персональная информация\n"
    first_name = resume_data.get('first_name', '')
    last_name = resume_data.get('last_name', '')
    middle_name = resume_data.get('middle_name', '')
    
    if first_name or last_name:
        full_name = ' '.join(filter(None, [first_name, middle_name, last_name]))
        formatted_text += f"Кандидат: {full_name}\n"
    
    # Текущая специализация
    formatted_text += f"Текущая специализация: {resume_data.get('title', 'Не указана')}\n"
    
    # Общий опыт работы
    total_experience = resume_data.get('total_experience')
    if total_experience:
        # total_experience может быть числом или словарем
        if isinstance(total_experience, dict):
            total_months = total_experience.get('months', 0) or 0
        else:
            total_months = total_experience
        
        if total_months > 0:
            years = total_months // 12
            months = total_months % 12
            exp_text = f"{years} лет" if years > 0 else ""
            if months > 0:
                exp_text += f" {months} месяцев" if exp_text else f"{months} месяцев"
            formatted_text += f"Общий опыт работы: {exp_text}\n"
    formatted_text += "\n"
    
    # Профессиональные роли
    professional_roles = resume_data.get('professional_roles', [])
    if professional_roles:
        formatted_text += "### Профессиональные роли\n"
        for role in professional_roles:
            if isinstance(role, dict):
                formatted_text += f"- {role.get('name', '')}\n"
            else:
                formatted_text += f"- {role}\n"
        formatted_text += "\n"
    
    # Общее описание навыков
    formatted_text += "### Общее описание профессиональных навыков\n"
    formatted_text += f"{resume_data.get('skills', 'Не указаны')}\n\n"
    
    # Умная категоризация технических навыков
    formatted_text += "### Технологический стек кандидата\n"
    skill_set = resume_data.get('skill_set', [])
    
    if skill_set:
        # Категоризация навыков
        programming_languages = [skill for skill in skill_set if any(word in skill.lower() 
                                    for word in ['python', 'javascript', 'java', 'c++', 'c#', 'php', 'go', 'rust', 'kotlin', 'swift', 'typescript', 'scala', 'ruby'])]
        
        frameworks_tools = [skill for skill in skill_set if any(word in skill.lower() 
                            for word in ['react', 'vue', 'angular', 'django', 'flask', 'spring', 'laravel', 'express', 'fastapi', 'nestjs', 'nextjs', 'nuxt'])]
        
        databases = [skill for skill in skill_set if any(word in skill.lower() 
                       for word in ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'clickhouse', 'cassandra', 'oracle'])]
        
        cloud_devops = [skill for skill in skill_set if any(word in skill.lower() 
                                for word in ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'gitlab', 'terraform', 'ansible'])]
        
        # Остальные навыки
        categorized_skills = programming_languages + frameworks_tools + databases + cloud_devops
        other_skills = [skill for skill in skill_set if skill not in categorized_skills]
        
        if programming_languages:
            formatted_text += f"**Языки программирования:** {', '.join(programming_languages)}\n"
        if frameworks_tools:
            formatted_text += f"**Фреймворки и библиотеки:** {', '.join(frameworks_tools)}\n"
        if databases:
            formatted_text += f"**Базы данных:** {', '.join(databases)}\n"
        if cloud_devops:
            formatted_text += f"**Cloud/DevOps:** {', '.join(cloud_devops)}\n"
        if other_skills:
            formatted_text += f"**Другие технологии:** {', '.join(other_skills[:10])}\n"  # Ограничиваем 10 навыками
    else:
        formatted_text += "Технические навыки не указаны\n"
    formatted_text += "\n"
    
    # Детальный анализ карьерной траектории
    formatted_text += "### Карьерная траектория и профессиональный опыт\n"
    experience_list = resume_data.get('experience', [])
    total_positions = len(experience_list)
    
    formatted_text += f"**Общее количество позиций:** {total_positions}\n"
    
    if experience_list:
        latest_position = experience_list[0] if experience_list else {}
        formatted_text += f"**Последняя позиция:** {latest_position.get('position', 'Не указана')}\n"
        
        # Анализ прогрессии в карьере
        if total_positions > 1:
            formatted_text += "\n**Карьерная прогрессия (последние позиции):**\n"
            for i, exp in enumerate(experience_list[:4], 1):  # Первые 4 позиции
                company = exp.get('company', 'Компания не указана')
                position = exp.get('position', 'Должность не указана')
                start = exp.get('start', '')
                end = exp.get('end', 'по настоящее время')
                formatted_text += f"  {i}. {position} в {company} ({start} - {end})\n"
        
        # Детальное описание ключевого опыта
        formatted_text += "\n**Детальное описание опыта:**\n"
        for i, exp in enumerate(experience_list[:3], 1):  # Топ-3 позиции
            company = exp.get('company', 'Компания не указана')
            position = exp.get('position', 'Должность не указана')
            start = exp.get('start', '')
            end = exp.get('end', 'по настоящее время')
            description = exp.get('description', 'Описание отсутствует')
            
            formatted_text += f"\n**Позиция #{i}: {position}**\n"
            formatted_text += f"Компания: {company}\n"
            formatted_text += f"Период: {start} - {end}\n"
            formatted_text += f"Описание проектов и задач: {description}\n"
    else:
        formatted_text += "Опыт работы не указан\n"
    formatted_text += "\n"
    
    # Образование и сертификация
    education = resume_data.get('education')
    certificates = resume_data.get('certificate', [])
    
    if education or certificates:
        formatted_text += "### Образование и сертификация\n"
        
        # Основное образование
        if education:
            primary = education.get('primary', [])
            if primary:
                formatted_text += "**Высшее образование:**\n"
                for edu in primary:
                    name = edu.get('name', 'Учебное заведение не указано')
                    result = edu.get('result', '')
                    year = edu.get('year', '')
                    formatted_text += f"- {name}"
                    if result:
                        formatted_text += f" - {result}"
                    if year:
                        formatted_text += f" ({year})"
                    formatted_text += "\n"
                
            # Дополнительное образование
            additional = education.get('additional', [])
            if additional:
                formatted_text += "\n**Дополнительное образование:**\n"
                for edu in additional[:5]:  # Первые 5
                    name = edu.get('name', 'Курс не указан')
                    organization = edu.get('organization', '')
                    year = edu.get('year', '')
                    formatted_text += f"- {name}"
                    if organization:
                        formatted_text += f" ({organization})"
                    if year:
                        formatted_text += f" - {year}"
                    formatted_text += "\n"
        
        # Сертификаты
        if certificates:
            formatted_text += "\n**Сертификаты:**\n"
            for cert in certificates[:5]:  # Первые 5 сертификатов
                title = cert.get('title', 'Сертификат не указан')
                url = cert.get('url', '')
                formatted_text += f"- {title}"
                if url:
                    formatted_text += f" (ссылка: {url})"
                formatted_text += "\n"
        
        formatted_text += "\n"
    
    # Языки (важно для многих позиций)
    languages = resume_data.get('languages', [])
    if languages:
        formatted_text += "### Знание языков\n"
        for lang in languages:
            name = lang.get('name', '')
            level = lang.get('level', {})
            if isinstance(level, dict):
                level_name = level.get('name', '')
            else:
                level_name = str(level)
            formatted_text += f"- {name}: {level_name}\n"
        formatted_text += "\n"
    
    # Онлайн-присутствие и портфолио
    sites = resume_data.get('site', [])
    if sites:
        formatted_text += "### Онлайн-присутствие и портфолио\n"
        for site in sites:
            site_type = site.get('type', {})
            if isinstance(site_type, dict):
                type_name = site_type.get('name', 'Сайт')
            else:
                type_name = str(site_type)
            url = site.get('url', '')
            formatted_text += f"- {type_name}: {url}\n"
        formatted_text += "\n"
    
    # Предпочтения и требования кандидата
    formatted_text += "### Предпочтения и требования кандидата\n"
    
    employments = resume_data.get('employments', [])
    if employments:
        # employments может содержать словари или строки
        emp_names = []
        for emp in employments:
            if isinstance(emp, dict):
                emp_names.append(emp.get('name', '') or emp.get('id', '') or str(emp))
            else:
                emp_names.append(str(emp))
        formatted_text += f"**Предпочитаемый тип занятости:** {', '.join(emp_names)}\n"
    
    schedules = resume_data.get('schedules', [])
    if schedules:
        # schedules может содержать словари или строки
        sch_names = []
        for sch in schedules:
            if isinstance(sch, dict):
                sch_names.append(sch.get('name', '') or sch.get('id', '') or str(sch))
            else:
                sch_names.append(str(sch))
        formatted_text += f"**Предпочитаемый график:** {', '.join(sch_names)}\n"
    
    salary = resume_data.get('salary', {})
    if salary and salary.get('amount'):
        formatted_text += f"**Зарплатные ожидания:** {salary.get('amount'):,} руб.\n"
    
    relocation = resume_data.get('relocation')
    if relocation:
        relocation_type = relocation.get('type', {})
        if isinstance(relocation_type, dict):
            type_name = relocation_type.get('name', '')
            if type_name:
                formatted_text += f"**Готовность к релокации:** {type_name}\n"
    
    return formatted_text


def format_vacancy_for_interview_prep(vacancy_data: Dict[str, Any]) -> str:
    """
    Форматирует данные вакансии для понимания требований к кандидату.
    Объединяет базовый и детальный анализ для полной картины.
    
    Args:
        vacancy_data: Словарь с данными вакансии
        
    Returns:
        str: Форматированный текст вакансии для анализа требований
    """
    formatted_text = "## ПОЛНЫЙ АНАЛИЗ ТРЕБОВАНИЙ ЦЕЛЕВОЙ ПОЗИЦИИ\n\n"
    
    # Основная информация о вакансии
    formatted_text += "### Основная информация о позиции\n"
    formatted_text += f"**Название позиции:** {vacancy_data.get('name', 'Не указано')}\n"
    formatted_text += f"**Компания:** {vacancy_data.get('company_name', 'Не указана')}\n"
    
    # Анализ требуемых профессиональных ролей
    professional_roles = vacancy_data.get('professional_roles', [])
    if professional_roles:
        formatted_text += "**Требуемые профессиональные роли:**\n"
        for role in professional_roles:
            if isinstance(role, dict):
                formatted_text += f"- {role.get('name', '')}\n"
            else:
                formatted_text += f"- {role}\n"
    formatted_text += "\n"
    
    # Полное описание вакансии с умным анализом
    description = vacancy_data.get('description', '')
    formatted_text += "### Детальный анализ описания вакансии\n"
    formatted_text += f"**Описание:** {description}\n\n"
    
    # Умный анализ требований из описания
    if description:
        description_lower = description.lower()
        
        formatted_text += "### Скрытые требования и особенности позиции\n"
        
        detected_requirements = []
        
        # Определение уровня сложности задач
        if any(word in description_lower for word in ['архитектур', 'проектирование', 'system design', 'lead', 'техлид', 'архитектор']):
            detected_requirements.append("🏗️ **Архитектурный уровень** - требуются навыки проектирования и системного дизайна")
        
        if any(word in description_lower for word in ['алгоритм', 'оптимизация', 'performance', 'высокие нагрузки', 'производительность']):
            detected_requirements.append("⚡ **Оптимизация и алгоритмы** - важны навыки работы с производительностью")
        
        if any(word in description_lower for word in ['команд', 'лидерство', 'менторство', 'team lead', 'руководство', 'управление']):
            detected_requirements.append("👥 **Лидерские навыки** - требуется опыт работы с командой и менторства")
        
        if any(word in description_lower for word in ['английский', 'english', 'международн', 'иностранн']):
            detected_requirements.append("🌍 **Английский язык** - необходимо знание английского языка")
        
        if any(word in description_lower for word in ['удален', 'remote', 'гибрид', 'hybrid']):
            detected_requirements.append("🏠 **Удаленная работа** - требуются навыки самоорганизации")
        
        if any(word in description_lower for word in ['стартап', 'startup', 'быстр', 'динамич']):
            detected_requirements.append("🚀 **Стартап-среда** - важна гибкость и многозадачность")
        
        if any(word in description_lower for word in ['agile', 'scrum', 'kanban', 'спринт']):
            detected_requirements.append("📋 **Agile-методологии** - опыт работы в гибких методологиях")
        
        if detected_requirements:
            for req in detected_requirements:
                formatted_text += f"{req}\n"
        else:
            formatted_text += "Специфических скрытых требований не обнаружено\n"
        formatted_text += "\n"

    # Детальный анализ ключевых навыков с категоризацией
    formatted_text += "### Детальный анализ требуемых навыков\n"
    key_skills = vacancy_data.get('key_skills', [])
    
    if key_skills:
        # Категоризация навыков из вакансии
        programming_languages = []
        frameworks_tools = []
        databases_storage = []
        cloud_devops = []
        methodologies = []
        soft_skills = []
        
        for skill in key_skills:
            # skill может быть строкой или словарем
            if isinstance(skill, dict):
                skill_name = skill.get('name', '') or skill.get('title', '') or str(skill)
            else:
                skill_name = str(skill)
            
            skill_lower = skill_name.lower()
            
            if any(lang in skill_lower for lang in ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'typescript', 'kotlin', 'swift']):
                programming_languages.append(skill_name)
            elif any(tool in skill_lower for tool in ['react', 'vue', 'angular', 'django', 'spring', 'flask', 'express', 'fastapi']):
                frameworks_tools.append(skill_name)
            elif any(db in skill_lower for db in ['sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch']):
                databases_storage.append(skill_name)
            elif any(cloud in skill_lower for cloud in ['docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'terraform']):
                cloud_devops.append(skill_name)
            elif any(method in skill_lower for method in ['agile', 'scrum', 'kanban', 'devops', 'ci/cd']):
                methodologies.append(skill_name)
            else:
                soft_skills.append(skill_name)
        
        if programming_languages:
            formatted_text += f"**Языки программирования:** {', '.join(programming_languages)}\n"
        if frameworks_tools:
            formatted_text += f"**Фреймворки и инструменты:** {', '.join(frameworks_tools)}\n"
        if databases_storage:
            formatted_text += f"**Базы данных и хранилища:** {', '.join(databases_storage)}\n"
        if cloud_devops:
            formatted_text += f"**Cloud/DevOps технологии:** {', '.join(cloud_devops)}\n"
        if methodologies:
            formatted_text += f"**Методологии и процессы:** {', '.join(methodologies)}\n"
        if soft_skills:
            formatted_text += f"**Дополнительные навыки:** {', '.join(soft_skills)}\n"
    else:
        formatted_text += "Ключевые навыки не указаны в вакансии\n"
    formatted_text += "\n"
    
    # Детальный анализ требований к опыту
    formatted_text += "### Требования к опыту и фокус интервью\n"
    
    experience = vacancy_data.get('experience', {})
    if experience and experience.get('id'):
        exp_id = experience.get('id')
        exp_mapping = {
            'noExperience': '**Уровень:** Начинающий специалист (без опыта)\n**Фокус интервью:** Потенциал, обучаемость, базовые знания, мотивация',
            'between1And3': '**Уровень:** Junior/Middle специалист (1-3 года)\n**Фокус интервью:** Практические навыки, реальные проекты, способность к развитию',
            'between3And6': '**Уровень:** Middle/Senior специалист (3-6 лет)\n**Фокус интервью:** Архитектурные решения, опыт лидерства, сложные проекты',
            'moreThan6': '**Уровень:** Senior+ специалист (6+ лет)\n**Фокус интервью:** Экспертные знания, лидерские качества, стратегическое мышление'
        }
        exp_text = exp_mapping.get(exp_id, f"Опыт: {exp_id}")
        formatted_text += f"{exp_text}\n\n"
    
    # Анализ формата работы и его влияния на интервью
    schedule = vacancy_data.get('schedule', {})
    employment = vacancy_data.get('employment', {})
    
    work_format_insights = []
    
    if schedule and schedule.get('id'):
        sch_id = schedule.get('id')
        if sch_id == 'remote':
            work_format_insights.append("**Удаленная работа** → Важны навыки самоорганизации, коммуникации в чатах, управления временем")
        elif sch_id == 'flexible':
            work_format_insights.append("**Гибкий график** → Требуется ответственность, планирование, результативность")
        elif sch_id == 'fullDay':
            work_format_insights.append("**Полный день** → Стандартный офисный формат, важна командная работа")
    
    if employment and employment.get('id'):
        emp_id = employment.get('id')
        if emp_id == 'project':
            work_format_insights.append("**Проектная работа** → Умение быстро включаться в задачи, самостоятельность")
        elif emp_id == 'probation':
            work_format_insights.append("**Стажировка** → Фокус на обучаемость, потенциал, желание развиваться")
    
    if work_format_insights:
        formatted_text += "### Особенности формата работы\n"
        for insight in work_format_insights:
            formatted_text += f"{insight}\n"
        formatted_text += "\n"
    
    return formatted_text