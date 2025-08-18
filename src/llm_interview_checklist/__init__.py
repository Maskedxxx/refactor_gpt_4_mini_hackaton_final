# src/llm_interview_checklist/__init__.py
# --- agent_meta ---
# role: llm-interview-checklist-init
# owner: @backend
# contract: Инициализация модуля генерации профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - Автоматическая регистрация при импорте модуля
# --- /agent_meta ---

"""
Модуль генерации профессионального чек-листа подготовки к интервью.

Предоставляет:
- Персонализированные чек-листы на основе HR-экспертизы
- Адаптацию под уровень кандидата (JUNIOR/MIDDLE/SENIOR/LEAD)
- Специализацию под тип роли (DEVELOPER/QA/DATA_SPECIALIST и др.)
- Настройку под формат компании (STARTUP/MEDIUM/LARGE_CORP/INTERNATIONAL)
- 7 блоков профессиональной подготовки: техническая, поведенческая, изучение компании, стек, практика, настройка окружения, дополнительные действия

Использование через унифицированное API: POST /features/interview_checklist/generate
"""

# Автоматическая регистрация фичи при импорте модуля
try:
    from .bootstrap import register_interview_checklist_feature
    register_interview_checklist_feature()
except Exception:
    # Graceful degradation если нет OpenAI ключа или другие проблемы
    pass

# Экспорт основных компонентов для внешнего использования
from .service import LLMInterviewChecklistGenerator
from .models import ProfessionalInterviewChecklist
from .options import InterviewChecklistOptions

__all__ = [
    "LLMInterviewChecklistGenerator",
    "ProfessionalInterviewChecklist", 
    "InterviewChecklistOptions",
]