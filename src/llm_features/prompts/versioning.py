# src/llm_features/prompts/versioning.py
# --- agent_meta ---
# role: llm-features-prompt-versioning
# owner: @backend
# contract: Версионируемые шаблоны промптов для всех LLM-фич
# last_reviewed: 2025-08-15
# interfaces:
#   - VersionedPromptTemplate (расширенный PromptTemplate с версионированием)
#   - PromptTemplateRegistry (реестр шаблонов по фичам и версиям)
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Optional, Callable
from dataclasses import dataclass

from src.parsing.llm.prompt import PromptTemplate, Prompt
from src.utils import get_logger
from ..base.errors import PromptBuildError


@dataclass
class VersionedPromptTemplate:
    """Версионируемый шаблон промпта для фичи."""
    feature_name: str
    version: str
    system_template: str
    user_template: str
    description: str = ""
    
    def render(self, context: Dict[str, any]) -> Prompt:
        """Рендер промпта с контекстом."""
        try:
            base_template = PromptTemplate(
                name=self.feature_name,
                version=self.version,
                system_tmpl=self.system_template,
                user_tmpl=self.user_template
            )
            return base_template.render(context)
        except Exception as e:
            raise PromptBuildError(f"Failed to render prompt {self.feature_name}@{self.version}: {str(e)}") from e


class PromptTemplateRegistry:
    """Реестр версионируемых шаблонов промптов.
    
    Позволяет:
    - Регистрировать шаблоны для фич с версиями
    - Получать шаблоны по имени фичи и версии
    - Динамически создавать шаблоны через фабрики
    """
    
    def __init__(self):
        self._log = get_logger(__name__)
        # templates[feature_name][version] = VersionedPromptTemplate or factory
        self._templates: Dict[str, Dict[str, VersionedPromptTemplate | Callable[[], VersionedPromptTemplate]]] = {}
        self._default_versions: Dict[str, str] = {}
    
    def register_template(
        self,
        feature_name: str,
        version: str,
        template: VersionedPromptTemplate | Callable[[], VersionedPromptTemplate],
        *,
        set_as_default: bool = False
    ) -> None:
        """Зарегистрировать шаблон для фичи."""
        if feature_name not in self._templates:
            self._templates[feature_name] = {}
        
        self._templates[feature_name][version] = template
        
        if set_as_default or feature_name not in self._default_versions:
            self._default_versions[feature_name] = version
        
        self._log.debug("Зарегистрирован шаблон %s@%s", feature_name, version)
    
    def get_template(
        self,
        feature_name: str,
        version: Optional[str] = None
    ) -> VersionedPromptTemplate:
        """Получить шаблон по имени фичи и версии."""
        # Определяем версию
        if version is None:
            version = self._default_versions.get(feature_name, "v1")
        
        # Проверяем существование
        if feature_name not in self._templates:
            raise PromptBuildError(f"No templates found for feature '{feature_name}'")
        
        if version not in self._templates[feature_name]:
            available_versions = list(self._templates[feature_name].keys())
            raise PromptBuildError(
                f"Template '{feature_name}@{version}' not found. "
                f"Available versions: {available_versions}"
            )
        
        template_or_factory = self._templates[feature_name][version]
        
        # Если это фабрика, вызываем её
        if callable(template_or_factory):
            try:
                template = template_or_factory()
                self._log.debug("Создан шаблон из фабрики: %s@%s", feature_name, version)
            except Exception as e:
                raise PromptBuildError(f"Factory failed for {feature_name}@{version}: {str(e)}") from e
        else:
            template = template_or_factory
        
        return template
    
    def list_templates(self) -> Dict[str, list[str]]:
        """Получить список всех фич и их версий."""
        return {
            feature_name: list(versions.keys())
            for feature_name, versions in self._templates.items()
        }


# Глобальный реестр шаблонов
_global_template_registry = PromptTemplateRegistry()


def get_template_registry() -> PromptTemplateRegistry:
    """Получить глобальный реестр шаблонов."""
    return _global_template_registry