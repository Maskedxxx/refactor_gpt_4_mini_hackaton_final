# src/llm_interview_checklist/prompts/mappings.py
# --- agent_meta ---
# role: llm-interview-checklist-prompt-mappings
# owner: @backend
# contract: Маппинги для динамической адаптации промптов подготовки к интервью по уровню кандидата, типу роли и формату компании
# last_reviewed: 2025-08-18
# interfaces:
#   - CANDIDATE_LEVEL_MAPPING
#   - VACANCY_TYPE_MAPPING
#   - COMPANY_FORMAT_MAPPING
#   - ROLE_DETECTION_KEYWORDS
#   - get_candidate_level_guidance()
#   - get_vacancy_type_adaptation()
#   - get_company_format_adaptation()
#   - detect_vacancy_type_from_description()
#   - analyze_candidate_level()
# --- /agent_meta ---

from __future__ import annotations

import re
from typing import Optional, Dict

from ..models import CandidateLevel, VacancyType, CompanyFormat


# Маппинг подходов по уровню кандидата
CANDIDATE_LEVEL_MAPPING = {
    CandidateLevel.JUNIOR: {
        "focus": "базовые знания, потенциал, обучаемость",
        "technical_depth": "фундаментальные основы, простые алгоритмы, понимание базовых концепций",
        "behavioral_focus": "мотивация, готовность учиться, работа в команде, следование инструкциям",
        "preparation_style": "акцент на изучение основ, больше времени на теорию, простые практические задачи",
        "interview_tips": "демонстрация энтузиазма, примеры обучения новому, готовность к фидбеку",
    },
    CandidateLevel.MIDDLE: {
        "focus": "практические навыки, самостоятельность, рост компетенций",
        "technical_depth": "углубленные знания стека, архитектурные паттерны, оптимизация решений",
        "behavioral_focus": "инициативность, решение проблем, mentoring junior'ов, ownership задач",
        "preparation_style": "баланс теории и практики, сложные алгоритмы, системный дизайн",
        "interview_tips": "конкретные примеры проектов, влияние на команду, принятие технических решений",
    },
    CandidateLevel.SENIOR: {
        "focus": "экспертные знания, лидерство, архитектурные решения",
        "technical_depth": "высокоуровневый дизайн, масштабирование, выбор технологий, trade-offs",
        "behavioral_focus": "техническое лидерство, менторство, стратегическое мышление, влияние на продукт",
        "preparation_style": "системный дизайн, сложные кейсы, архитектурные решения",
        "interview_tips": "демонстрация экспертизы, примеры лидерства, влияние на бизнес-метрики",
    },
    CandidateLevel.LEAD: {
        "focus": "управление командой, стратегическое планирование, процессы",
        "technical_depth": "архитектура больших систем, технологические стратегии, code review процессы",
        "behavioral_focus": "управление людьми, планирование roadmap, работа со stakeholders",
        "preparation_style": "управленческие кейсы, процессы разработки, планирование и приоритизация",
        "interview_tips": "примеры управления командой, улучшения процессов, достижения KPI команды",
    },
}

# Маппинг адаптации по типу вакансии
VACANCY_TYPE_MAPPING = {
    VacancyType.DEVELOPER: {
        "key_areas": "алгоритмы, структуры данных, архитектурные паттерны, code review",
        "technical_focus": "практическое программирование, оптимизация производительности, чистый код",
        "behavioral_aspects": "работа в команде разработки, code review, техническая коммуникация",
        "typical_questions": "coding challenges, system design, архитектурные решения",
        "preparation_resources": "LeetCode, System Design Interview, архитектурные книги",
    },
    VacancyType.QA_ENGINEER: {
        "key_areas": "методологии тестирования, автоматизация, инструменты QA, процессы качества",
        "technical_focus": "test design, automation frameworks, bug lifecycle, performance testing",
        "behavioral_aspects": "внимание к деталям, коммуникация с разработчиками, advocacy качества",
        "typical_questions": "тест-кейсы, стратегии тестирования, автоматизация, багрепорты",
        "preparation_resources": "ISTQB материалы, automation frameworks, testing tools",
    },
    VacancyType.DATA_SPECIALIST: {
        "key_areas": "статистика, машинное обучение, анализ данных, визуализация",
        "technical_focus": "Python/R/SQL, ML алгоритмы, статистические методы, big data",
        "behavioral_aspects": "работа с бизнесом, презентация инсайтов, исследовательский подход",
        "typical_questions": "data cases, ML algorithms, статистические тесты, business metrics",
        "preparation_resources": "Kaggle, ML курсы, статистические книги, business case studies",
    },
    VacancyType.BUSINESS_ANALYST: {
        "key_areas": "анализ требований, процессы, документирование, работа со stakeholders",
        "technical_focus": "SQL, BI tools, process modeling, requirements engineering",
        "behavioral_aspects": "коммуникация с бизнесом, facilitation, конфликт-резолюция",
        "typical_questions": "process improvement, requirements gathering, stakeholder management",
        "preparation_resources": "BABOK, process modeling, business analysis courses",
    },
    VacancyType.DESIGNER: {
        "key_areas": "UX research, design systems, прототипирование, пользовательские метрики",
        "technical_focus": "design tools, user research methods, accessibility, design systems",
        "behavioral_aspects": "эмпатия к пользователям, collaboration с разработчиками, презентация идей",
        "typical_questions": "design process, user research, portfolio review, design decisions",
        "preparation_resources": "portfolio update, UX research methods, design principles",
    },
    VacancyType.DEVOPS: {
        "key_areas": "автоматизация, CI/CD, инфраструктура, мониторинг, надежность",
        "technical_focus": "containerization, orchestration, IaC, monitoring, security",
        "behavioral_aspects": "автоматизация процессов, incident response, cross-team collaboration",
        "typical_questions": "infrastructure design, automation strategies, incident handling",
        "preparation_resources": "cloud certifications, IaC tools, monitoring platforms",
    },
    VacancyType.MANAGER: {
        "key_areas": "планирование, управление командой, процессы, метрики, delivery",
        "technical_focus": "project management tools, agile methodologies, metrics tracking",
        "behavioral_aspects": "лидерство, мотивация команды, conflict resolution, strategic thinking",
        "typical_questions": "team management, process improvement, delivery challenges",
        "preparation_resources": "management books, agile courses, leadership materials",
    },
    VacancyType.OTHER: {
        "key_areas": "специфичные для роли компетенции",
        "technical_focus": "relevant technical skills for the position",
        "behavioral_aspects": "role-specific soft skills and competencies",
        "typical_questions": "role-specific scenarios and technical questions",
        "preparation_resources": "industry-specific materials and resources",
    },
}

# Маппинг адаптации по формату компании
COMPANY_FORMAT_MAPPING = {
    CompanyFormat.STARTUP: {
        "culture_focus": "быстрые решения, ownership, гибкость, многозадачность",
        "interview_style": "неформальный, фокус на потенциал и адаптивность",
        "key_qualities": "самостоятельность, готовность к изменениям, инициативность",
        "preparation_tips": "демонстрация гибкости, примеры быстрого обучения, ownership проектов",
        "typical_environment": "небольшие команды, прямая коммуникация, быстрые итерации",
    },
    CompanyFormat.MEDIUM_COMPANY: {
        "culture_focus": "баланс процессов и гибкости, командная работа, рост",
        "interview_style": "структурированный, но человечный подход",
        "key_qualities": "профессиональный рост, командная работа, качество результата",
        "preparation_tips": "примеры работы в команде, фокус на качество, планирование развития",
        "typical_environment": "сбалансированные процессы, командная работа, развитие карьеры",
    },
    CompanyFormat.LARGE_CORP: {
        "culture_focus": "процессы, масштабируемость, стабильность, соответствие стандартам",
        "interview_style": "формальный, структурированный, несколько этапов",
        "key_qualities": "следование процессам, системный подход, долгосрочное планирование",
        "preparation_tips": "знание корпоративных процессов, examples of scale, compliance awareness",
        "typical_environment": "четкие процессы, большие команды, долгосрочные проекты",
    },
    CompanyFormat.INTERNATIONAL: {
        "culture_focus": "культурное разнообразие, удаленная работа, английский язык",
        "interview_style": "мультикультурный, часто на английском, time zone challenges",
        "key_qualities": "кросс-культурная коммуникация, английский язык, remote work skills",
        "preparation_tips": "английский язык, примеры удаленной работы, cultural awareness",
        "typical_environment": "международные команды, удаленная работа, английский как рабочий язык",
    },
}

# Ключевые слова для автоопределения типа вакансии
ROLE_DETECTION_KEYWORDS = {
    VacancyType.DEVELOPER: [
        "разработчик", "developer", "программист", "software engineer", "backend", "frontend",
        "fullstack", "mobile", "android", "ios", "python", "java", "javascript", "react",
        "vue", "angular", "node.js", "django", "spring", "программное обеспечение"
    ],
    VacancyType.QA_ENGINEER: [
        "тестировщик", "qa", "quality assurance", "test engineer", "автотестировщик",
        "тестирование", "качество", "automation", "selenium", "cypress", "testing"
    ],
    VacancyType.DATA_SPECIALIST: [
        "data scientist", "data analyst", "аналитик данных", "machine learning", "ml engineer",
        "big data", "python", "pandas", "numpy", "sql", "статистика", "анализ данных"
    ],
    VacancyType.BUSINESS_ANALYST: [
        "бизнес-аналитик", "business analyst", "системный аналитик", "product analyst",
        "требования", "процессы", "аналитик", "analyst"
    ],
    VacancyType.DESIGNER: [
        "дизайнер", "designer", "ux", "ui", "продуктовый дизайнер", "веб-дизайнер",
        "graphic designer", "figma", "sketch", "прототипирование"
    ],
    VacancyType.DEVOPS: [
        "devops", "sre", "системный администратор", "infrastructure", "docker",
        "kubernetes", "aws", "azure", "ci/cd", "jenkins", "terraform"
    ],
    VacancyType.MANAGER: [
        "менеджер", "manager", "руководитель", "team lead", "project manager",
        "продукт менеджер", "scrum master", "лидер", "lead"
    ],
}


def get_candidate_level_guidance(level: CandidateLevel) -> Dict[str, str]:
    """Получить руководство по подготовке для заданного уровня кандидата."""
    return CANDIDATE_LEVEL_MAPPING.get(level, CANDIDATE_LEVEL_MAPPING[CandidateLevel.MIDDLE])


def get_vacancy_type_adaptation(vacancy_type: VacancyType) -> Dict[str, str]:
    """Получить адаптацию подготовки для заданного типа вакансии."""
    return VACANCY_TYPE_MAPPING.get(vacancy_type, VACANCY_TYPE_MAPPING[VacancyType.OTHER])


def get_company_format_adaptation(company_format: CompanyFormat) -> Dict[str, str]:
    """Получить адаптацию подготовки для заданного формата компании."""
    return COMPANY_FORMAT_MAPPING.get(company_format, COMPANY_FORMAT_MAPPING[CompanyFormat.MEDIUM_COMPANY])


def detect_vacancy_type_from_description(title: str, description: str) -> Optional[VacancyType]:
    """
    Автоопределение типа вакансии по названию и описанию.
    
    Args:
        title: Название позиции
        description: Описание вакансии
        
    Returns:
        Определенный тип вакансии или None если не удалось определить
    """
    text_to_analyze = f"{title} {description}".lower()
    
    # Проверяем каждый тип вакансии
    for vacancy_type, keywords in ROLE_DETECTION_KEYWORDS.items():
        for keyword in keywords:
            # Используем регулярные выражения для более точного поиска
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_to_analyze):
                return vacancy_type
    
    return VacancyType.OTHER


def analyze_candidate_level(experience_data: list, total_experience_months: int) -> CandidateLevel:
    """
    Анализ уровня кандидата на основе опыта работы.
    
    Args:
        experience_data: Список позиций из резюме
        total_experience_months: Общий опыт в месяцах
        
    Returns:
        Определенный уровень кандидата
    """
    years_of_experience = total_experience_months / 12 if total_experience_months else 0
    
    # Анализ лидерских позиций
    has_leadership_experience = False
    if experience_data:
        for position in experience_data:
            position_title = position.get('position', '').lower()
            if any(word in position_title for word in ['lead', 'лид', 'руководитель', 'manager', 'менеджер', 'senior']):
                has_leadership_experience = True
                break
    
    # Определение уровня
    if has_leadership_experience and years_of_experience >= 5:
        return CandidateLevel.LEAD
    elif years_of_experience >= 6:
        return CandidateLevel.SENIOR
    elif years_of_experience >= 3:
        return CandidateLevel.MIDDLE
    else:
        return CandidateLevel.JUNIOR


def detect_company_format(company_name: str, description: str) -> CompanyFormat:
    """
    Определение формата компании по названию и описанию.
    
    Args:
        company_name: Название компании
        description: Описание вакансии/компании
        
    Returns:
        Определенный формат компании
    """
    text_to_analyze = f"{company_name} {description}".lower()
    
    # Ключевые слова для определения формата
    startup_keywords = ['стартап', 'startup', 'растущая команда', 'молодая компания', 'быстрый рост']
    large_corp_keywords = ['корпорация', 'enterprise', 'крупная компания', 'международная корпорация', 'глобальная компания']
    international_keywords = ['international', 'global', 'worldwide', 'multinational', 'удаленная работа', 'remote']
    
    if any(keyword in text_to_analyze for keyword in startup_keywords):
        return CompanyFormat.STARTUP
    elif any(keyword in text_to_analyze for keyword in large_corp_keywords):
        return CompanyFormat.LARGE_CORP
    elif any(keyword in text_to_analyze for keyword in international_keywords):
        return CompanyFormat.INTERNATIONAL
    else:
        return CompanyFormat.MEDIUM_COMPANY


if __name__ == "__main__":
    """Интерактивное тестирование функций mappings.py"""
    
    # Тестирование определения типа вакансии
    print("detect_vacancy_type_from_description('Senior Python Developer', 'backend development'):")
    print(detect_vacancy_type_from_description('Senior Python Developer', 'backend development'))
    print()
    
    # Тестирование анализа уровня кандидата
    print("analyze_candidate_level([{'position': 'Senior Developer'}], 72):")
    print(analyze_candidate_level([{'position': 'Senior Developer'}], 72))
    print()
    
    # Тестирование адаптации по типу вакансии
    print("get_vacancy_type_adaptation(VacancyType.DEVELOPER):")
    adaptation = get_vacancy_type_adaptation(VacancyType.DEVELOPER)
    for key, value in adaptation.items():
        print(f"  {key}: {value}")
    print()
    
    print("# Замените значения выше на нужные для тестирования")