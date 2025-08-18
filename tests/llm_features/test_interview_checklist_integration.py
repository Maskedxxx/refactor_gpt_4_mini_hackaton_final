# tests/llm_features/test_interview_checklist_integration.py
# --- agent_meta ---
# role: llm-interview-checklist-integration-test
# owner: @backend
# contract: Интеграционные тесты фичи interview_checklist через FeatureRegistry и универсальное API
# last_reviewed: 2025-08-18
# interfaces:
#   - test_interview_checklist_full_pipeline()
#   - test_interview_checklist_via_webapp_api()
#   - test_interview_checklist_registry_integration()
# --- /agent_meta ---

import os
import json
from unittest.mock import patch, AsyncMock

import pytest

from src.llm_features.registry import get_global_registry
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_interview_checklist.options import InterviewChecklistOptions
from src.llm_interview_checklist.models import ProfessionalInterviewChecklist

# Импортируем фикстуры из webapp
from tests.webapp.conftest import app_ctx, async_client  # noqa: F401


@pytest.fixture
def sample_test_data():
    """Загружаем минимальные валидные тестовые данные из JSON файлов."""
    test_dir = os.path.join(os.path.dirname(__file__), "../data")

    with open(os.path.join(test_dir, "simple_resume.json")) as f:
        resume_data = json.load(f)

    with open(os.path.join(test_dir, "simple_vacancy.json")) as f:
        vacancy_data = json.load(f)

    return {
        "resume": ResumeInfo(**resume_data),
        "vacancy": VacancyInfo(**vacancy_data),
    }


@pytest.fixture
def mock_checklist_response() -> ProfessionalInterviewChecklist:
    """Загружаем валидный мок результата interview_checklist (строго по модели)."""
    data_path = os.path.join(os.path.dirname(__file__), "../data/interview_checklist_result_6423ab26.json")
    with open(data_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return ProfessionalInterviewChecklist.model_validate(payload)


@pytest.mark.asyncio
async def test_interview_checklist_full_pipeline(sample_test_data, mock_checklist_response):
    """Тест полного пайплайна генерации interview_checklist через FeatureRegistry."""

    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()

        with patch("src.llm_interview_checklist.service.LLMInterviewChecklistGenerator._call_llm") as mock_llm_call:
            mock_llm_call.return_value = mock_checklist_response

            registry = get_global_registry()
            generator = registry.get_generator("interview_checklist", version="v1")

            options = InterviewChecklistOptions(
                temperature=0.3,
                language="ru",
            )

            result = await generator.generate(
                sample_test_data["resume"],
                sample_test_data["vacancy"],
                options,
            )

            assert isinstance(result, ProfessionalInterviewChecklist)
            assert result.personalization_context.candidate_level == "SENIOR"
            assert len(result.technical_preparation) > 0
            mock_llm_call.assert_called_once()


@pytest.mark.asyncio
async def test_interview_checklist_via_webapp_api(async_client, sample_test_data, mock_checklist_response):
    """Тест генерации interview_checklist через универсальное API webapp."""

    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()

        with patch("src.llm_interview_checklist.service.LLMInterviewChecklistGenerator._call_llm") as mock_llm_call:
            mock_llm_call.return_value = mock_checklist_response

            request_data = {
                "resume": sample_test_data["resume"].model_dump(),
                "vacancy": sample_test_data["vacancy"].model_dump(),
                "options": {
                    "temperature": 0.3,
                    "language": "ru",
                },
            }

            response = await async_client.post(
                "/features/interview_checklist/generate",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["feature_name"] == "interview_checklist"
            assert "result" in data
            assert isinstance(data["result"].get("technical_preparation"), list)


@pytest.mark.asyncio
async def test_interview_checklist_registry_integration():
    """Проверяем, что фича interview_checklist автоматически зарегистрирована в реестре."""
    registry = get_global_registry()
    feature_names = registry.get_feature_names()
    assert "interview_checklist" in feature_names

