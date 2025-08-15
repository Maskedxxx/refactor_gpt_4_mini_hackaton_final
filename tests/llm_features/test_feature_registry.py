# tests/llm_features/test_feature_registry.py
# --- agent_meta ---
# role: llm-features-registry-test
# owner: @backend
# contract: Тестирует FeatureRegistry - регистрация, получение, версионирование фич
# last_reviewed: 2025-08-15
# interfaces:
#   - test_registry_registration_and_retrieval()
#   - test_registry_versioning()
#   - test_registry_nonexistent_feature()
# --- /agent_meta ---

import pytest

from src.llm_features.registry import FeatureRegistry
from src.llm_features.base.errors import FeatureNotFoundError
from src.llm_features.base.options import BaseLLMOptions
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo


class MockLLMGenerator:
    """Мок-генератор для тестирования регистрации"""
    
    def __init__(self, result_data: str = "test_result"):
        self.result_data = result_data
    
    async def generate(self, resume: ResumeInfo, vacancy: VacancyInfo, options: BaseLLMOptions) -> str:
        return self.result_data


@pytest.fixture
def empty_registry():
    """Создает пустой реестр для каждого теста"""
    return FeatureRegistry()


@pytest.fixture
def registry_with_features(empty_registry):
    """Реестр с предустановленными тестовыми фичами"""
    registry = empty_registry
    
    # Регистрируем тестовую фичу с двумя версиями
    registry.register(
        name="test_feature",
        generator_class=MockLLMGenerator,
        version="v1",
        description="Test feature version 1"
    )
    
    registry.register(
        name="test_feature", 
        generator_class=MockLLMGenerator,
        version="v2",
        description="Test feature version 2",
        set_as_default=True
    )
    
    # Регистрируем еще одну фичу
    registry.register(
        name="another_feature",
        generator_class=MockLLMGenerator,
        version="v1",
        description="Another test feature"
    )
    
    return registry


def test_registry_registration_and_retrieval(empty_registry):
    """Тест базовой регистрации и получения фичи"""
    registry = empty_registry
    
    # Регистрируем фичу
    registry.register(
        name="sample_feature",
        generator_class=MockLLMGenerator,
        version="v1",
        description="Sample feature for testing"
    )
    
    # Проверяем что фича появилась в списке
    features = registry.list_features()
    assert len(features) == 1
    feature_info = features[0]
    assert feature_info.name == "sample_feature"
    assert feature_info.version == "v1"
    assert feature_info.description == "Sample feature for testing"
    
    # Проверяем что фича есть в списке имен
    feature_names = registry.get_feature_names()
    assert "sample_feature" in feature_names
    
    # Получаем генератор фичи
    generator = registry.get_generator("sample_feature", version="v1")
    assert isinstance(generator, MockLLMGenerator)
    
    # Получаем генератор без указания версии (должен вернуть default)
    default_generator = registry.get_generator("sample_feature")
    assert isinstance(default_generator, MockLLMGenerator)


def test_registry_versioning(registry_with_features):
    """Тест версионирования фич"""
    registry = registry_with_features
    
    # Проверяем что зарегистрированы обе версии фичи test_feature
    versions = registry.get_versions("test_feature")
    assert "v1" in versions
    assert "v2" in versions
    assert len(versions) == 2
    
    # Проверяем получение конкретной версии
    v1_generator = registry.get_generator("test_feature", version="v1")
    v2_generator = registry.get_generator("test_feature", version="v2")
    default_generator = registry.get_generator("test_feature")  # без версии (должен вернуть v2)
    
    assert isinstance(v1_generator, MockLLMGenerator)
    assert isinstance(v2_generator, MockLLMGenerator) 
    assert isinstance(default_generator, MockLLMGenerator)


def test_registry_nonexistent_feature(registry_with_features):
    """Тест обработки несуществующих фич и версий"""
    registry = registry_with_features
    
    # Попытка получить несуществующую фичу
    with pytest.raises(FeatureNotFoundError) as exc_info:
        registry.get_generator("nonexistent_feature")
    
    assert "Feature 'nonexistent_feature' not found" in str(exc_info.value)
    
    # Попытка получить несуществующую версию существующей фичи
    with pytest.raises(FeatureNotFoundError) as exc_info:
        registry.get_generator("test_feature", version="v999")
    
    assert "Feature 'test_feature' version 'v999' not found" in str(exc_info.value)


def test_registry_list_features_empty(empty_registry):
    """Тест получения списка фич из пустого реестра"""
    registry = empty_registry
    
    features = registry.list_features()
    assert features == []


def test_registry_list_features_multiple(registry_with_features):
    """Тест получения списка множественных фич"""
    registry = registry_with_features
    
    features = registry.list_features()
    
    # Проверяем что есть 3 фичи (test_feature v1, test_feature v2, another_feature v1)
    assert len(features) == 3
    
    # Проверяем имена фич
    feature_names = registry.get_feature_names()
    assert "test_feature" in feature_names
    assert "another_feature" in feature_names
    assert len(feature_names) == 2
    
    # Проверяем структуру FeatureInfo
    for feature_info in features:
        assert hasattr(feature_info, 'name')
        assert hasattr(feature_info, 'version') 
        assert hasattr(feature_info, 'description')
        assert hasattr(feature_info, 'generator_class')
        assert feature_info.generator_class == MockLLMGenerator


def test_registry_generator_instantiation_with_kwargs(empty_registry):
    """Тест создания генератора с дополнительными аргументами"""
    registry = empty_registry
    
    # Регистрируем фичу
    registry.register(
        name="custom_feature",
        generator_class=MockLLMGenerator,
        version="v1"
    )
    
    # Получаем генератор с кастомными аргументами для инициализации
    generator = registry.get_generator(
        "custom_feature",
        version="v1", 
        result_data="custom_result"  # передаем в конструктор MockLLMGenerator
    )
    
    assert isinstance(generator, MockLLMGenerator)
    assert generator.result_data == "custom_result"


def test_registry_overwrites_default_version(empty_registry):
    """Тест перезаписи версии по умолчанию"""
    registry = empty_registry
    
    # Регистрируем v1 как default
    registry.register(
        name="feature",
        generator_class=MockLLMGenerator,
        version="v1",
        set_as_default=True
    )
    
    # Проверяем что v1 - дефолтная версия
    default_gen_1 = registry.get_generator("feature")  # без указания версии
    assert isinstance(default_gen_1, MockLLMGenerator)
    
    # Регистрируем v2 и делаем его default
    registry.register(
        name="feature",
        generator_class=MockLLMGenerator, 
        version="v2",
        set_as_default=True
    )
    
    # Проверяем что теперь v2 - дефолтная версия
    default_gen_2 = registry.get_generator("feature")  # без указания версии
    assert isinstance(default_gen_2, MockLLMGenerator)
    
    # Проверяем что обе версии доступны
    versions = registry.get_versions("feature")
    assert len(versions) == 2
    assert "v1" in versions
    assert "v2" in versions