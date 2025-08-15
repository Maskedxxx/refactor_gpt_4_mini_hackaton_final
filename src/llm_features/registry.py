# src/llm_features/registry.py
# --- agent_meta ---
# role: llm-features-registry
# owner: @backend
# contract: Реестр LLM-фич с поддержкой версионирования и динамической регистрации
# last_reviewed: 2025-08-15
# interfaces:
#   - FeatureRegistry.register(name, generator_class, version)
#   - FeatureRegistry.get_generator(name, version) -> ILLMGenerator
#   - FeatureRegistry.list_features() -> List[FeatureInfo]
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass

from src.utils import get_logger
from .base.interfaces import ILLMGenerator
from .base.errors import FeatureNotFoundError, FeatureRegistrationError


@dataclass
class FeatureInfo:
    """Информация о зарегистрированной фиче."""
    name: str
    version: str
    generator_class: Type[ILLMGenerator]
    default_config: Dict[str, Any]
    description: str = ""


class FeatureRegistry:
    """Реестр LLM-фич с поддержкой версионирования.
    
    Поддерживает:
    - Регистрацию фич с версиями
    - Получение генераторов по имени и версии
    - Автоматическое создание экземпляров с DI
    - Список доступных фич
    """
    
    def __init__(self):
        self._log = get_logger(__name__)
        # features[name][version] = FeatureInfo
        self._features: Dict[str, Dict[str, FeatureInfo]] = {}
        # Дефолтные версии для каждой фичи
        self._default_versions: Dict[str, str] = {}
    
    def register(
        self,
        name: str,
        generator_class: Type[ILLMGenerator],
        version: str = "v1",
        *,
        default_config: Optional[Dict[str, Any]] = None,
        description: str = "",
        set_as_default: bool = False
    ) -> None:
        """Зарегистрировать фичу в реестре.
        
        Args:
            name: Название фичи (например, 'cover_letter')
            generator_class: Класс генератора
            version: Версия фичи 
            default_config: Дефолтная конфигурация
            description: Описание фичи
            set_as_default: Установить как дефолтную версию
        """
        try:
            if name not in self._features:
                self._features[name] = {}
            
            # Проверяем, что класс реализует нужный интерфейс
            if not hasattr(generator_class, 'generate'):
                raise FeatureRegistrationError(
                    name, 
                    f"Generator class {generator_class.__name__} must implement ILLMGenerator"
                )
            
            feature_info = FeatureInfo(
                name=name,
                version=version, 
                generator_class=generator_class,
                default_config=default_config or {},
                description=description
            )
            
            self._features[name][version] = feature_info
            
            # Устанавливаем дефолтную версию
            if set_as_default or name not in self._default_versions:
                self._default_versions[name] = version
                
            self._log.info(
                "Зарегистрирована фича: %s@%s (класс=%s)", 
                name, version, generator_class.__name__
            )
            
        except Exception as e:
            raise FeatureRegistrationError(name, str(e)) from e
    
    def get_generator(
        self, 
        name: str, 
        version: Optional[str] = None,
        **init_kwargs
    ) -> ILLMGenerator:
        """Получить экземпляр генератора фичи.
        
        Args:
            name: Название фичи
            version: Версия (если не указана, используется дефолтная)
            **init_kwargs: Параметры для конструктора генератора
        """
        # Определяем версию
        if version is None:
            version = self._default_versions.get(name)
            if version is None:
                raise FeatureNotFoundError(name)
        
        # Проверяем существование фичи
        if name not in self._features or version not in self._features[name]:
            raise FeatureNotFoundError(name, version)
        
        feature_info = self._features[name][version]
        
        # Создаем экземпляр с дефолтной конфигурацией + параметрами пользователя
        config = {**feature_info.default_config, **init_kwargs}
        
        try:
            generator = feature_info.generator_class(**config)
            self._log.debug("Создан генератор %s@%s", name, version)
            return generator
        except Exception as e:
            self._log.error("Ошибка создания генератора %s@%s: %s", name, version, str(e))
            raise FeatureRegistrationError(name, f"Failed to create generator: {str(e)}") from e
    
    def list_features(self) -> List[FeatureInfo]:
        """Получить список всех зарегистрированных фич."""
        features = []
        for feature_name, versions in self._features.items():
            for version, feature_info in versions.items():
                features.append(feature_info)
        return features
    
    def get_feature_names(self) -> List[str]:
        """Получить список названий всех фич."""
        return list(self._features.keys())
    
    def get_versions(self, feature_name: str) -> List[str]:
        """Получить список версий для конкретной фичи."""
        if feature_name not in self._features:
            raise FeatureNotFoundError(feature_name)
        return list(self._features[feature_name].keys())
    
    def unregister(self, name: str, version: Optional[str] = None) -> None:
        """Удалить фичу из реестра."""
        if name not in self._features:
            raise FeatureNotFoundError(name)
        
        if version is None:
            # Удаляем всю фичу со всеми версиями
            del self._features[name]
            if name in self._default_versions:
                del self._default_versions[name]
            self._log.info("Удалена фича: %s (все версии)", name)
        else:
            # Удаляем конкретную версию
            if version not in self._features[name]:
                raise FeatureNotFoundError(name, version)
            
            del self._features[name][version]
            
            # Если удалили дефолтную версию, выбираем новую
            if self._default_versions.get(name) == version:
                remaining_versions = list(self._features[name].keys())
                if remaining_versions:
                    self._default_versions[name] = remaining_versions[0]
                else:
                    del self._default_versions[name]
            
            self._log.info("Удалена фича: %s@%s", name, version)


# Глобальный экземпляр реестра
_global_registry = FeatureRegistry()


def get_global_registry() -> FeatureRegistry:
    """Получить глобальный экземпляр реестра фич."""
    return _global_registry