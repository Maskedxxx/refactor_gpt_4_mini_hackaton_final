# tests/llm_features/test_features_api.py
# --- agent_meta ---
# role: llm-features-api-test
# owner: @backend
# contract: Тестирует универсальные API роуты для LLM фич (/features/*)
# last_reviewed: 2025-08-15
# interfaces:
#   - test_get_features_list()
#   - test_feature_generation_success()
#   - test_feature_generation_not_found()
# --- /agent_meta ---

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.llm_features.base.errors import FeatureNotFoundError
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo

# Импортируем фикстуры из webapp
from tests.webapp.conftest import async_client, app_ctx


class MockLLMGenerator:
    """Мок-генератор для тестирования API"""
    
    def __init__(self, result_data="test_result"):
        self.result_data = result_data
    
    async def generate(self, resume: ResumeInfo, vacancy: VacancyInfo, options):
        # Возвращаем мок-результат
        return {"content": self.result_data, "generated": True}


@pytest.fixture
def mock_registry():
    """Создает мок-реестр с тестовыми фичами"""
    from src.llm_features.registry import FeatureInfo
    
    registry = MagicMock()
    
    # Создаем реальный FeatureInfo объект (не мок)
    mock_feature_info = FeatureInfo(
        name="test_feature",
        version="v1",
        generator_class=MockLLMGenerator,
        default_config={},
        description="Test feature"
    )
    
    registry.list_features.return_value = [mock_feature_info]
    registry.get_feature_names.return_value = ["test_feature"]
    registry.get_versions.return_value = ["v1"]
    
    return registry


@pytest.fixture 
def sample_request_data():
    """Тестовые данные для запроса генерации (только обязательные поля)"""
    import json
    import os
    
    # Загружаем реальные тестовые данные
    test_dir = os.path.join(os.path.dirname(__file__), "../data")
    
    with open(os.path.join(test_dir, "simple_resume.json")) as f:
        resume = json.load(f)
        
    with open(os.path.join(test_dir, "simple_vacancy.json")) as f:
        vacancy = json.load(f)
    
    return {
        "resume": resume,
        "vacancy": vacancy,
        "options": {
            "temperature": 0.4,
            "language": "ru"
        }
    }


@pytest.mark.asyncio
async def test_get_features_list(async_client, mock_registry):
    """Тест получения списка доступных фич"""
    
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        response = await async_client.get("/features/")
    
    assert response.status_code == 200
    data = response.json()
    
    # Проверяем структуру ответа
    assert "features" in data
    assert isinstance(data["features"], dict)
    
    # В моке у нас одна фича
    mock_registry.list_features.assert_called_once()


@pytest.mark.asyncio 
async def test_feature_generation_success(async_client, mock_registry, sample_request_data):
    """Тест успешной генерации через фичу"""
    
    # Мокаем успешное получение генератора
    mock_generator = MockLLMGenerator("Generated cover letter")
    mock_registry.get_generator.return_value = mock_generator
    
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        response = await async_client.post(
            "/features/test_feature/generate",
            json=sample_request_data
        )
    
    if response.status_code != 200:
        print("Response status:", response.status_code)
        print("Response body:", response.text)
    
    assert response.status_code == 200
    data = response.json()
    print("Response data:", data)
    
    # Проверяем что результат содержит ожидаемые поля  
    assert "result" in data
    assert "feature_name" in data
    assert data["feature_name"] == "test_feature"
    
    # Генератор возвращает dict, но API сериализует в строку через str()
    # Поэтому проверяем что в result.output содержится нужная строка
    result_output = data["result"]["output"]  
    assert "Generated cover letter" in result_output
    
    # Проверяем что вызван правильный метод реестра
    mock_registry.get_generator.assert_called_once_with("test_feature", version=None)


@pytest.mark.asyncio
async def test_feature_generation_not_found(async_client, mock_registry, sample_request_data):
    """Тест обработки несуществующей фичи"""
    
    # Мокаем исключение при попытке получить несуществующую фичу
    mock_registry.get_generator.side_effect = FeatureNotFoundError("nonexistent_feature")
    
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        response = await async_client.post(
            "/features/nonexistent_feature/generate", 
            json=sample_request_data
        )
    
    assert response.status_code == 404
    data = response.json()
    
    assert "detail" in data
    assert "nonexistent_feature" in data["detail"]


@pytest.mark.asyncio 
async def test_feature_generation_with_version(async_client, mock_registry, sample_request_data):
    """Тест генерации с указанием конкретной версии"""
    
    mock_generator = MockLLMGenerator("Version v2 result")
    mock_registry.get_generator.return_value = mock_generator
    
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        response = await async_client.post(
            "/features/test_feature/generate?version=v2",
            json=sample_request_data
        )
    
    assert response.status_code == 200
    data = response.json()
    # API сериализует dict как строку, поэтому проверяем что наш результат содержится в строке
    result_output = data["result"]["output"]
    assert "Version v2 result" in result_output
    
    # Проверяем что версия была передана
    mock_registry.get_generator.assert_called_once_with("test_feature", version="v2")


@pytest.mark.asyncio
async def test_feature_generation_invalid_request_data(async_client, mock_registry):
    """Тест обработки невалидных данных запроса"""
    
    invalid_data = {
        "resume": {},  # пустое резюме
        "vacancy": {},  # пустая вакансия
        # отсутствуют options
    }
    
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        response = await async_client.post(
            "/features/test_feature/generate",
            json=invalid_data
        )
    
    # Ожидаем ошибку валидации (422 Unprocessable Entity или аналогично)
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_feature_generation_internal_error(async_client, mock_registry, sample_request_data):
    """Тест обработки внутренней ошибки генератора"""
    
    # Мокаем генератор который падает с исключением
    mock_generator = AsyncMock()
    mock_generator.generate.side_effect = Exception("Internal generator error")
    mock_registry.get_generator.return_value = mock_generator
    
    with patch("src.webapp.features.get_global_registry", return_value=mock_registry):
        response = await async_client.post(
            "/features/test_feature/generate",
            json=sample_request_data
        )
    
    # Ожидаем 500 Internal Server Error
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data