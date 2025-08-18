# src/llm_interview_checklist/bootstrap.py
# --- agent_meta ---
# role: llm-interview-checklist-bootstrap
# owner: @backend
# contract: Регистрация генератора чек-листа подготовки к интервью в FeatureRegistry
# last_reviewed: 2025-08-18
# interfaces:
#   - register_interview_checklist_feature()
# --- /agent_meta ---

from src.llm_features.registry import get_global_registry
from src.utils import get_logger

from .service import LLMInterviewChecklistGenerator

logger = get_logger()


def register_interview_checklist_feature():
    """
    Регистрирует генератор профессионального чек-листа подготовки к интервью 
    в глобальном реестре LLM-фич.
    """
    try:
        registry = get_global_registry()
        
        # Регистрируем генератор чек-листа
        registry.register(
            name="interview_checklist",
            generator_class=LLMInterviewChecklistGenerator,
            version="v1",
            description="Персонализированный профессиональный чек-лист подготовки к IT-интервью на основе HR-экспертизы",
            set_as_default=True
        )
        
        logger.info("✅ Interview checklist feature registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register interview checklist feature: {e}")
        raise