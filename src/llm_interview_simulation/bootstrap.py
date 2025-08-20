# src/llm_interview_simulation/bootstrap.py
# --- agent_meta ---
# role: interview-simulation-bootstrap
# owner: @backend
# contract: Автоматическая регистрация фичи симуляции интервью в LLM Features Framework
# last_reviewed: 2025-08-18
# interfaces:
#   - register_interview_simulation_feature() (вызывается при импорте модуля)
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Any

from src.utils import get_logger
from src.llm_features.registry import get_global_registry, FeatureInfo
from src.llm_features.base.errors import FeatureRegistrationError

from .service import LLMInterviewSimulationGenerator
from .config import default_settings
from .options import InterviewSimulationOptions

logger = get_logger(__name__)


def register_interview_simulation_feature() -> None:
    """Регистрирует фичу симуляции интервью в глобальном реестре.
    
    Эта функция вызывается автоматически при импорте модуля и регистрирует
    генератор симуляции интервью в LLM Features Framework.
    
    Raises:
        FeatureRegistrationError: Если регистрация не удалась
    """
    try:
        logger.info("Регистрируем фичу симуляции интервью в реестре")
        
        # Получаем глобальный реестр фич
        registry = get_global_registry()
        
        # Создаем информацию о фиче
        feature_info = FeatureInfo(
            name=default_settings.feature_name,
            version=default_settings.feature_version,
            generator_class=LLMInterviewSimulationGenerator,
            default_config=_create_default_config(),
            description=default_settings.feature_description
        )
        
        # Регистрируем фичу в реестре
        registry.register(
            name=feature_info.name,
            generator_class=feature_info.generator_class,
            version=feature_info.version,
            default_config=feature_info.default_config,
            description=feature_info.description
        )
        
        logger.info(f"Фича '{default_settings.feature_name}' v{default_settings.feature_version} успешно зарегистрирована")
        
        # Логируем информацию о конфигурации
        logger.debug(f"Конфигурация фичи: {len(feature_info.default_config)} параметров")
        logger.debug(f"Поддерживаемые раунды: {default_settings.default_options.target_rounds}")
        logger.debug(f"Уровень сложности по умолчанию: {default_settings.default_options.difficulty_level}")
        
    except Exception as e:
        error_msg = f"Ошибка регистрации фичи симуляции интервью: {e}"
        logger.error(error_msg)
        raise FeatureRegistrationError(error_msg) from e


def _create_default_config() -> Dict[str, Any]:
    """Создает конфигурацию по умолчанию для фичи.
    
    Возвращает только параметры, которые действительно нужны для инициализации
    LLMInterviewSimulationGenerator (openai_api_key, openai_model_name, etc.).
    Параметры опций (target_rounds, difficulty_level, etc.) передаются через
    метод generate(), а не через конструктор.
    
    Returns:
        Dict[str, Any]: Словарь с настройками по умолчанию для конструктора
    """
    config = {
        # === Параметры для конструктора LLMInterviewSimulationGenerator ===
        # Все параметры опций убираются, т.к. они передаются через generate()
        
        # Конструктор LLMInterviewSimulationGenerator принимает только:
        # llm, validator, formatter, openai_api_key, openai_model_name
        # Все остальные параметры (опции) передаются через generate()
    }
    
    logger.debug(f"Создана конфигурация по умолчанию с {len(config)} параметрами")
    return config


def get_feature_info() -> FeatureInfo:
    """Возвращает информацию о зарегистрированной фиче.
    
    Returns:
        FeatureInfo: Информация о фиче симуляции интервью
    """
    return FeatureInfo(
        name=default_settings.feature_name,
        version=default_settings.feature_version,
        generator_class=LLMInterviewSimulationGenerator,
        default_config=_create_default_config(),
        description=default_settings.feature_description
    )


def create_generator_with_options(options: Dict[str, Any]) -> LLMInterviewSimulationGenerator:
    """Создает экземпляр генератора с заданными опциями.
    
    Args:
        options: Словарь с опциями для настройки генератора
        
    Returns:
        LLMInterviewSimulationGenerator: Настроенный генератор
    """
    logger.debug(f"Создаем генератор с опциями: {list(options.keys())}")
    
    # Извлекаем настройки OpenAI из опций или используем дефолтные
    openai_api_key = options.get('openai_api_key', default_settings.openai_api_key)
    openai_model_name = options.get('openai_model_name', default_settings.openai_model_name)
    
    # Создаем генератор
    generator = LLMInterviewSimulationGenerator(
        openai_api_key=openai_api_key,
        openai_model_name=openai_model_name
    )
    
    logger.debug("Генератор симуляции интервью создан")
    return generator


def validate_options(options: Dict[str, Any]) -> InterviewSimulationOptions:
    """Валидирует и создает объект опций из словаря.
    
    Args:
        options: Словарь с опциями
        
    Returns:
        InterviewSimulationOptions: Валидированные опции
        
    Raises:
        ValueError: Если опции некорректны
    """
    try:
        # Создаем объект опций из словаря
        interview_options = InterviewSimulationOptions(**options)
        
        logger.debug(f"Опции валидированы: {interview_options.target_rounds} раундов, {interview_options.difficulty_level}")
        return interview_options
        
    except Exception as e:
        error_msg = f"Некорректные опции для симуляции интервью: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e


# Функция для интеграции с существующими системами
def create_simulation_context(resume_data: Dict[str, Any], 
                             vacancy_data: Dict[str, Any],
                             options: Dict[str, Any]) -> Dict[str, Any]:
    """Создает контекст для симуляции интервью.
    
    Эта функция помогает интегрироваться с существующими системами,
    которые работают со словарями вместо Pydantic моделей.
    
    Args:
        resume_data: Данные резюме в формате словаря
        vacancy_data: Данные вакансии в формате словаря 
        options: Опции симуляции
        
    Returns:
        Dict[str, Any]: Контекст для передачи в генератор
    """
    logger.debug("Создаем контекст симуляции интервью")
    
    # Валидируем опции
    validated_options = validate_options(options)
    
    # Создаем контекст
    context = {
        'resume_data': resume_data,
        'vacancy_data': vacancy_data,
        'options': validated_options,
        'feature_name': default_settings.feature_name,
        'feature_version': default_settings.feature_version
    }
    
    logger.debug(f"Контекст создан для позиции: {vacancy_data.get('name', 'неизвестно')}")
    return context


# Автоматический вызов регистрации при импорте модуля
logger.info("Инициализируем модуль симуляции интервью...")

try:
    register_interview_simulation_feature()
    logger.info("Модуль симуляции интервью инициализирован успешно")
except Exception as e:
    logger.error(f"Ошибка инициализации модуля симуляции интервью: {e}")
    # Не поднимаем исключение, чтобы не сломать импорт всего приложения
