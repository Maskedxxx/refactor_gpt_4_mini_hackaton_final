# src/llm_cover_letter/prompts/mappings.py
# --- agent_meta ---
# role: llm-cover-letter-prompt-mappings
# owner: @backend
# contract: Маппинги для динамической адаптации промптов по размеру компании и типу роли
# last_reviewed: 2025-08-14
# interfaces:
#   - COMPANY_TONE_MAPPING
#   - ROLE_ADAPTATION_MAPPING
#   - ROLE_DETECTION_KEYWORDS
#   - get_company_tone_instruction()
#   - get_role_adaptation_instruction()
#   - detect_role_from_title()
# --- /agent_meta ---

from __future__ import annotations

import re
from typing import Optional

from ..models import RoleType


# Маппинг тональности по размеру компании
COMPANY_TONE_MAPPING = {
    "STARTUP": (
        "более неформально, энтузиазм, готовность к вызовам. "
        "Подчеркивай адаптивность, готовность к быстрым изменениям, "
        "стремление влиять на продукт с первых дней."
    ),
    "MEDIUM": (
        "баланс профессионализма и человечности. "
        "Показывай зрелый подход к работе, готовность к команде, "
        "фокус на качестве и стабильном росте."
    ),
    "LARGE": (
        "баланс профессионализма и человечности. "
        "Демонстрируй системный подход, опыт работы в больших командах, "
        "понимание масштабируемости и процессов."
    ),
    "ENTERPRISE": (
        "максимально профессионально, стабильность. "
        "Подчеркивай надежность, соответствие стандартам, "
        "опыт работы с комплаенсом и корпоративными процедурами."
    ),
}

# Маппинг адаптации по типу роли
ROLE_ADAPTATION_MAPPING = {
    RoleType.DEVELOPER: {
        "definition": "Backend/Frontend/Mobile разработчик, программист, software engineer.",
        "adaptation": (
            "Фокусируйтесь на техническом стеке, проектах, производительности, "
            "code review, архитектуре. Упоминайте конкретные технологии, "
            "паттерны проектирования, оптимизации кода."
        ),
    },
    RoleType.ML_ENGINEER: {
        "definition": "ML engineer, AI engineer, machine learning, deep learning, computer vision.",
        "adaptation": (
            "Фокусируйтесь на алгоритмах ML, моделях, пайплайнах, экспериментах, "
            "метриках качества. Упоминайте фреймворки (TensorFlow, PyTorch), "
            "feature engineering, model deployment."
        ),
    },
    RoleType.DATA_SCIENTIST: {
        "definition": "Data scientist, аналитик данных, исследователь данных, big data.",
        "adaptation": (
            "Фокусируйтесь на исследованиях, статистике, инсайтах, A/B тестах, "
            "бизнес-метриках. Подчеркивайте влияние анализа на бизнес-решения, "
            "работу с большими данными."
        ),
    },
    RoleType.QA_ENGINEER: {
        "definition": "Тестировщик, QA, quality assurance, автотестировщик, test engineer.",
        "adaptation": (
            "Фокусируйтесь на внимании к деталям, критических багах, "
            "инструментах тестирования, качестве. Упоминайте тест-планы, "
            "автоматизацию, регрессионное тестирование."
        ),
    },
    RoleType.ANALYST: {
        "definition": "Бизнес-аналитик, системный аналитик, product analyst, BI analyst.",
        "adaptation": (
            "Фокусируйтесь на требованиях, процессах, домене, улучшениях "
            "бизнес-метрик, аналитике. Подчеркивайте навыки работы с stakeholders, "
            "документирование процессов."
        ),
    },
    RoleType.DEVOPS: {
        "definition": "DevOps, SRE, системный администратор, infrastructure, cloud engineer.",
        "adaptation": (
            "Фокусируйтесь на автоматизации, надежности, экономии времени/ресурсов, "
            "инфраструктуре. Упоминайте CI/CD, мониторинг, облачные решения, "
            "масштабирование системы."
        ),
    },
    RoleType.DESIGNER: {
        "definition": "UI/UX дизайнер, продуктовый дизайнер, веб-дизайнер, motion designer.",
        "adaptation": (
            "Фокусируйтесь на UX-метриках, портфолио, влиянии на конверсию, "
            "пользовательском опыте. Упоминайте дизайн-системы, прототипирование, "
            "user research."
        ),
    },
    RoleType.MANAGER: {
        "definition": "Project manager, team lead, product manager, scrum master, руководитель.",
        "adaptation": (
            "Фокусируйтесь на команде, процессах, результатах, лидерстве, "
            "управлении проектами. Подчеркивайте навыки мотивации команды, "
            "планирования, достижения KPI."
        ),
    },
    RoleType.OTHER: {
        "definition": "Если не подходит ни один из вышеперечисленных.",
        "adaptation": (
            "Опишите ключевые аспекты, специфичные для данной роли. "
            "Акцентируйте уникальные навыки и достижения кандидата."
        ),
    },
}

# Ключевые слова для автоопределения роли по названию должности
ROLE_DETECTION_KEYWORDS = {
    RoleType.DEVELOPER: [
        # Backend
        "backend", "бэкенд", "бекенд", "python", "java", "golang", "node.js", "nodejs",
        "developer", "разработчик", "программист", "software engineer", "инженер-программист",
        # Frontend  
        "frontend", "фронтенд", "фронт-енд", "react", "vue", "angular", "javascript", "js",
        "html", "css", "веб-разработчик", "web developer",
        # Mobile
        "mobile", "мобильный", "android", "ios", "flutter", "react native", "kotlin", "swift",
        # General
        "fullstack", "фулстек", "full stack", "full-stack",
    ],
    RoleType.ML_ENGINEER: [
        "ml engineer", "machine learning", "машинное обучение", "ai engineer", "artificial intelligence",
        "deep learning", "глубокое обучение", "computer vision", "компьютерное зрение", "nlp",
        "natural language processing", "обработка естественного языка", "tensorflow", "pytorch",
        "нейронные сети", "neural networks", "data mining", "ml", "ai", "ии",
    ],
    RoleType.DATA_SCIENTIST: [
        "data scientist", "ученый по данным", "исследователь данных", "аналитик данных",
        "big data", "большие данные", "статистик", "statistician", "research scientist",
        "data research", "pandas", "numpy", "scipy", "jupyter", "r", "matlab",
    ],
    RoleType.QA_ENGINEER: [
        "qa", "quality assurance", "тестировщик", "тестирование", "test engineer", "инженер по тестированию",
        "автотестировщик", "automation", "автоматизация тестирования", "selenium", "cypress",
        "качество", "quality", "testing", "qa engineer", "sdet",
    ],
    RoleType.ANALYST: [
        "аналитик", "analyst", "бизнес-аналитик", "business analyst", "системный аналитик", "system analyst",
        "product analyst", "продуктовый аналитик", "bi analyst", "business intelligence",
        "требования", "requirements", "процессы", "processes", "документирование",
    ],
    RoleType.DEVOPS: [
        "devops", "sre", "site reliability", "системный администратор", "sysadmin", "infrastructure",
        "инфраструктура", "cloud engineer", "облачный инженер", "aws", "azure", "gcp", "google cloud",
        "kubernetes", "docker", "ci/cd", "ansible", "terraform", "jenkins", "gitlab ci",
    ],
    RoleType.DESIGNER: [
        "designer", "дизайнер", "ui designer", "ux designer", "ui/ux", "продуктовый дизайнер",
        "product designer", "веб-дизайнер", "web designer", "графический дизайнер", "graphic designer",
        "motion designer", "моушн дизайнер", "figma", "sketch", "adobe", "прототипирование",
    ],
    RoleType.MANAGER: [
        "manager", "менеджер", "руководитель", "team lead", "тимлид", "лид", "lead",
        "project manager", "проект-менеджер", "product manager", "продакт менеджер",
        "scrum master", "скрам мастер", "agile", "управление", "лидер", "coordinator",
    ],
}


def get_company_tone_instruction(company_size: str) -> str:
    """Получить инструкцию по тональности для заданного размера компании."""
    return COMPANY_TONE_MAPPING.get(company_size, COMPANY_TONE_MAPPING["MEDIUM"])


def get_role_adaptation_instruction(role_type: RoleType) -> str:
    """Получить инструкцию по адаптации для заданного типа роли."""
    role_info = ROLE_ADAPTATION_MAPPING.get(role_type, ROLE_ADAPTATION_MAPPING[RoleType.OTHER])
    return f"**{role_type.value}**: {role_info['adaptation']}"


def detect_role_from_title(title: str) -> Optional[RoleType]:
    """Автоопределение типа роли по названию должности.
    
    Args:
        title: Название должности (например, "Senior Python Developer")
        
    Returns:
        Определенный тип роли или None если не удалось определить
    """
    if not title:
        return None
        
    title_lower = title.lower()
    
    # Проверяем каждый тип роли
    for role_type, keywords in ROLE_DETECTION_KEYWORDS.items():
        for keyword in keywords:
            # Используем регулярные выражения для более точного поиска
            # \b - границы слова, чтобы избежать ложных срабатываний
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, title_lower):
                return role_type
    
    return None


def get_role_definition(role_type: RoleType) -> str:
    """Получить определение роли."""
    role_info = ROLE_ADAPTATION_MAPPING.get(role_type, ROLE_ADAPTATION_MAPPING[RoleType.OTHER])
    return role_info['definition']


if __name__ == "__main__":
    """Интерактивное тестирование функций mappings.py"""
    
    # Автоопределение роли
    print("detect_role_from_title('Senior Python Developer'):")
    print(detect_role_from_title('Senior Python Developer'))
    print()
    
    # Тональность компании
    print("get_company_tone_instruction('STARTUP'):")
    print(get_company_tone_instruction('STARTUP'))
    print()
    
    # Адаптация роли
    print("get_role_adaptation_instruction(RoleType.DEVELOPER):")
    print(get_role_adaptation_instruction(RoleType.DEVELOPER))
    print()
    
    print("# Замените значения выше на нужные для тестирования")