# src/llm_interview_simulation/__init__.py
# --- agent_meta ---
# role: interview-simulation-init
# owner: @backend
# contract: Инициализация модуля симуляции интервью с автоматической регистрацией в LLM Features Framework
# last_reviewed: 2025-08-18
# interfaces:
#   - Автоматическая регистрация фичи при импорте
#   - Экспорт основных классов и функций
# --- /agent_meta ---

"""
Модуль симуляции интервью для LLM Features Framework.

Этот модуль предоставляет возможность проведения профессиональных симуляций
интервью между AI HR-менеджером и AI кандидатом на основе реального резюме и вакансии.

Основные возможности:
- Адаптивные вопросы в зависимости от уровня кандидата
- Структурированная оценка по компетенциям  
- Многораундовый диалог с различными типами вопросов
- Профессиональный анализ и рекомендации
- Интеграция с LLM Features Framework

Пример использования:
    from src.llm_interview_simulation import LLMInterviewSimulationGenerator
    
    generator = LLMInterviewSimulationGenerator()
    result = await generator.generate(resume, vacancy, options)
    # print(result)  # оценочные поля удалены

Автоматическая регистрация:
    При импорте этого модуля фича автоматически регистрируется в LLM Features Framework
    и становится доступной через стандартные API роуты.
"""

from .service import LLMInterviewSimulationGenerator
from .models import (
    InterviewSimulation,
    DialogMessage, 
    CandidateProfile,
    InterviewConfiguration,
    CandidateLevel,
    ITRole,
    QuestionType,
    CompetencyArea
)
from .options import InterviewSimulationOptions
from .config import default_settings
from .formatter import (
    format_resume_for_interview_simulation,
    format_vacancy_for_interview_simulation,
    create_candidate_profile_and_config
)
from .bootstrap import (
    register_interview_simulation_feature,
    get_feature_info,
    create_generator_with_options,
    validate_options
)

# Автоматическая регистрация фичи при импорте модуля
# (регистрация происходит в bootstrap.py при его импорте)
from . import bootstrap

__all__ = [
    # === Основные классы ===
    "LLMInterviewSimulationGenerator",
    "InterviewSimulation", 
    "DialogMessage",
    "CandidateProfile",
    "InterviewConfiguration",
    
    # === Перечисления ===
    "CandidateLevel",
    "ITRole", 
    "QuestionType",
    "CompetencyArea",
    
    # === Опции и настройки ===
    "InterviewSimulationOptions",
    "default_settings",
    
    # === Форматтеры ===
    "format_resume_for_interview_simulation",
    "format_vacancy_for_interview_simulation", 
    "create_candidate_profile_and_config",
    
    # === Функции bootstrap ===
    "register_interview_simulation_feature",
    "get_feature_info",
    "create_generator_with_options",
    "validate_options"
]

# Метаданные модуля
__version__ = default_settings.feature_version
__author__ = "LLM Features Framework"
__description__ = default_settings.feature_description

# Информация для интеграции
FEATURE_NAME = default_settings.feature_name
FEATURE_VERSION = default_settings.feature_version
SUPPORTED_VERSIONS = [FEATURE_VERSION]

# Конфигурация для внешних систем
DEFAULT_CONFIG = {
    "target_rounds": default_settings.default_options.target_rounds,
    "difficulty_level": default_settings.default_options.difficulty_level,
    "hr_personality": default_settings.default_options.hr_personality
}

# Проверка готовности модуля
def is_feature_registered() -> bool:
    """Проверяет, зарегистрирована ли фича в реестре.
    
    Returns:
        bool: True если фича зарегистрирована
    """
    try:
        from src.llm_features.registry import get_global_registry
        registry = get_global_registry()
        return registry.has_feature(FEATURE_NAME)
    except Exception:
        return False


def get_feature_status() -> dict:
    """Возвращает статус фичи для диагностики.
    
    Returns:
        dict: Информация о статусе фичи
    """
    return {
        "name": FEATURE_NAME,
        "version": FEATURE_VERSION, 
        "registered": is_feature_registered(),
        "config_keys": list(DEFAULT_CONFIG.keys()),
        "generator_class": LLMInterviewSimulationGenerator.__name__
    }
