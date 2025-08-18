# src/llm_interview_checklist/config.py
# --- agent_meta ---
# role: llm-interview-checklist-config
# owner: @backend
# contract: Конфигурация для сервиса генерации профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewChecklistSettings
#   - settings (глобальный экземпляр)
# --- /agent_meta ---

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.llm_features.config import BaseFeatureSettings


class InterviewChecklistSettings(BaseFeatureSettings):
    """
    Настройки для сервиса генерации профессионального чек-листа подготовки к интервью.
    Наследует базовые настройки и добавляет специфичные для данной фичи.
    """
    
    # Специфичные настройки для interview checklist
    default_preparation_time: str = Field(
        default="1 неделя",
        description="Время подготовки по умолчанию"
    )
    
    default_focus_depth: str = Field(
        default="comprehensive",
        description="Глубина анализа по умолчанию (basic, comprehensive, expert)"
    )
    
    # Базовые настройки наследуются от BaseFeatureSettings:
    # - model_name: str = "gpt-4o-mini-2024-07-18"
    # - temperature: float = 0.2 (консервативный для профессионального контента)
    # - prompt_version: str = "interview_checklist.v1"
    # - language: str = "ru"
    # - quality_checks: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="INTERVIEW_CHECKLIST_",  # INTERVIEW_CHECKLIST_MODEL_NAME, INTERVIEW_CHECKLIST_TEMPERATURE и т.д.
        extra="ignore"
    )


# Глобальный экземпляр настроек
settings = InterviewChecklistSettings()