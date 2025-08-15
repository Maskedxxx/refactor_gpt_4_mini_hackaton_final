# src/llm_cover_letter/bootstrap.py
# --- agent_meta ---
# role: llm-cover-letter-bootstrap
# owner: @backend
# contract: Регистрация фичи cover_letter в глобальном реестре
# last_reviewed: 2025-08-15
# interfaces:
#   - register_cover_letter_feature() -> None
# --- /agent_meta ---

from src.llm_features.registry import get_global_registry
from src.llm_features.prompts.versioning import get_template_registry, VersionedPromptTemplate
from .service import LLMCoverLetterGenerator
from .prompts.templates import get_template


def register_cover_letter_templates():
    """Регистрировать шаблоны промптов cover_letter в глобальном реестре."""
    template_registry = get_template_registry()
    
    # Регистрируем v1
    v1_template = get_template("cover_letter.v1")
    template_registry.register_template(
        "cover_letter",
        "v1", 
        VersionedPromptTemplate(
            feature_name="cover_letter",
            version="v1",
            system_template=v1_template._system_tmpl,
            user_template=v1_template._user_tmpl,
            description="Базовая версия промпта для сопроводительных писем"
        )
    )
    
    # Регистрируем v2  
    v2_template = get_template("cover_letter.v2")
    template_registry.register_template(
        "cover_letter", 
        "v2",
        VersionedPromptTemplate(
            feature_name="cover_letter",
            version="v2", 
            system_template=v2_template._system_tmpl,
            user_template=v2_template._user_tmpl,
            description="Улучшенная версия с HR методологией"
        ),
        set_as_default=True
    )


def register_cover_letter_feature():
    """Регистрировать фичу cover_letter в глобальном реестре."""
    registry = get_global_registry()
    
    # Сначала регистрируем шаблоны
    register_cover_letter_templates()
    
    # Регистрируем фичу
    registry.register(
        name="cover_letter",
        generator_class=LLMCoverLetterGenerator,
        version="v1",
        description="Генерация персонализированных сопроводительных писем"
    )
    
    # Регистрируем v2
    registry.register(
        name="cover_letter",
        generator_class=LLMCoverLetterGenerator, 
        version="v2",
        set_as_default=True,
        description="Генерация писем с улучшенной HR методологией"
    )