# tests/llm_features/test_interview_simulation_integration.py
# --- agent_meta ---
# role: llm-interview-simulation-integration-test
# owner: @backend
# contract: Интеграционные тесты фичи interview_simulation через FeatureRegistry и универсальное API + проверка опций/дефолтов
# last_reviewed: 2025-08-20
# interfaces:
#   - test_interview_simulation_full_pipeline()
#   - test_interview_simulation_via_webapp_api()
#   - test_interview_simulation_registry_integration()
#   - test_interview_simulation_options_merge_with_defaults()
#   - test_interview_simulation_yaml_rounds_precedence()
#   - test_interview_simulation_basic_formatted_output()
# --- /agent_meta ---

import os
import json
from unittest.mock import patch, AsyncMock

import pytest

# Инициируем импорт модуля для авто-регистрации фичи в реестре
import src.llm_interview_simulation  # noqa: F401

from src.llm_features.registry import get_global_registry
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo

from src.llm_interview_simulation.options import InterviewSimulationOptions
from src.llm_interview_simulation.models import InterviewSimulation
from src.llm_interview_simulation import default_settings

# Импортируем фикстуры из webapp
from tests.webapp.conftest import app_ctx, async_client  # noqa: F401


@pytest.fixture
def sample_test_data():
    """Загружаем минимальные валидные тестовые данные из JSON файлов."""
    test_dir = os.path.join(os.path.dirname(__file__), "../data")

    with open(os.path.join(test_dir, "simple_resume.json"), encoding="utf-8") as f:
        resume_data = json.load(f)

    with open(os.path.join(test_dir, "simple_vacancy.json"), encoding="utf-8") as f:
        vacancy_data = json.load(f)

    return {
        "resume": ResumeInfo(**resume_data),
        "vacancy": VacancyInfo(**vacancy_data),
    }


@pytest.fixture
def mock_simulation_response() -> InterviewSimulation:
    """Загружаем валидный мок результата interview_simulation (строго по модели)."""
    data_path = os.path.join(
        os.path.dirname(__file__),
        "../data/interview_simulation_result_20250820_104305.json",
    )
    with open(data_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return InterviewSimulation.model_validate(payload)


@pytest.mark.asyncio
async def test_interview_simulation_full_pipeline(sample_test_data, mock_simulation_response):
    """Тест полного пайплайна генерации interview_simulation через FeatureRegistry."""

    # Переопределяем OpenAI клиента и сам LLM вызов, чтобы не обращаться в сеть
    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()

        with patch(
            "src.llm_interview_simulation.service.LLMInterviewSimulationGenerator._call_llm"
        ) as mock_llm_call:
            mock_llm_call.return_value = mock_simulation_response

            registry = get_global_registry()
            # Версию не указываем: должна подхватиться дефолтная (из регистрации)
            generator = registry.get_generator("interview_simulation")

            options = InterviewSimulationOptions(
                temperature=0.5,
                language="ru",
                target_rounds=4,
                hr_personality="neutral",
            )

            result = await generator.generate(
                sample_test_data["resume"],
                sample_test_data["vacancy"],
                options,
            )

            assert isinstance(result, InterviewSimulation)
            # Проверяем ключевые поля результата, ожидаемые из фикстуры
            assert result.candidate_profile.detected_level == "lead"
            assert result.interview_config.target_rounds == 7
            assert len(result.dialog_messages) >= 2
            assert result.total_rounds_completed == 7
            mock_llm_call.assert_called_once()


@pytest.mark.asyncio
async def test_interview_simulation_via_webapp_api(
    async_client, sample_test_data, mock_simulation_response
):
    """Тест генерации interview_simulation через универсальное API webapp."""

    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()

        with patch(
            "src.llm_interview_simulation.service.LLMInterviewSimulationGenerator._call_llm"
        ) as mock_llm_call:
            mock_llm_call.return_value = mock_simulation_response

            request_data = {
                "resume": sample_test_data["resume"].model_dump(),
                "vacancy": sample_test_data["vacancy"].model_dump(),
                "options": {
                    "temperature": 0.6,
                    "language": "ru",
                    "target_rounds": 4,
                    "difficulty_level": "easy",
                },
            }

            response = await async_client.post(
                "/features/interview_simulation/generate",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["feature_name"] == "interview_simulation"
            assert "result" in data
            assert isinstance(data["result"].get("dialog_messages"), list)
            # Проверим, что заголовочные поля отданы и согласованы с фикстурой
            assert data["result"]["candidate_profile"]["detected_level"] == "lead"
            assert data["result"]["interview_config"]["target_rounds"] == 7


def test_interview_simulation_registry_integration():
    """Проверяем, что фича interview_simulation автоматически зарегистрирована в реестре с версией."""
    registry = get_global_registry()
    feature_names = registry.get_feature_names()
    assert "interview_simulation" in feature_names

    versions = registry.get_versions("interview_simulation")
    # Версия берется из default_settings.feature_version
    assert default_settings.feature_version in versions


def test_interview_simulation_options_merge_with_defaults():
    """Проверяем, что _merge_with_defaults заполняет пропуски согласно default_settings.default_options."""
    from src.llm_interview_simulation.service import LLMInterviewSimulationGenerator

    # Мокаем OpenAI клиент, чтобы избежать требования API ключа
    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        gen = LLMInterviewSimulationGenerator()

        # Создаем опции с минимальными валидными значениями, но некоторые поля можно переопределить через _merge_with_defaults
        partial = InterviewSimulationOptions(
            prompt_version="v1.0",
            target_rounds=3,  # минимальное валидное значение  
            difficulty_level="medium",
            # Оставляем другие поля дефолтными, чтобы проверить merge логику
        )

        merged = gen._merge_with_defaults(partial)

        defaults = default_settings.default_options
        # Проверяем, что заданные значения сохранились
        assert merged.prompt_version == "v1.0"
        assert merged.target_rounds == 3
        assert merged.difficulty_level == "medium"
        
        # Проверяем, что дефолтные поля подтянулись из настроек
        assert merged.temperature_hr == defaults.temperature_hr
        assert merged.temperature_candidate == defaults.temperature_candidate
        assert merged.hr_personality == defaults.hr_personality
        assert merged.candidate_confidence == defaults.candidate_confidence


def test_interview_simulation_yaml_rounds_precedence(monkeypatch):
    """Проверяем порядок переопределения: YAML > python defaults для количества раундов по уровню.

    Меняем app_config.feature_settings.target_rounds_by_level для senior и проверяем, что helper
    get_target_rounds_for_level возвращает значение из YAML вместо python дефолта.
    """
    from src.llm_interview_simulation.config import app_config, get_target_rounds_for_level
    from src.llm_interview_simulation.models import CandidateLevel

    # Убедимся, что дефолт для SENIOR в python — 6 (на случай регрессии)
    assert default_settings.level_rounds_mapping[CandidateLevel.SENIOR] == 6

    # Подменяем YAML-конфиг через monkeypatch
    patched = dict(app_config)
    patched.setdefault("feature_settings", {})["target_rounds_by_level"] = {
        "senior": 4
    }
    monkeypatch.setattr(
        "src.llm_interview_simulation.config.app_config",
        patched,
        raising=False,
    )

    # Теперь helper должен вернуть 4 вместо 6
    assert get_target_rounds_for_level(CandidateLevel.SENIOR) == 4


def test_interview_simulation_basic_formatted_output(mock_simulation_response):
    """Проверяем, что форматтер генератора выводит ключевые строки для пользователя."""
    from src.llm_interview_simulation.service import LLMInterviewSimulationGenerator

    # Мокаем OpenAI клиент, чтобы избежать требования API ключа
    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        gen = LLMInterviewSimulationGenerator()
        text = gen.format_for_output(mock_simulation_response)

        # Проверяем наличие ключевых фрагментов
        assert "=== СИМУЛЯЦИЯ ИНТЕРВЬЮ ===" in text
        assert "Уровень:" in text
        assert "Раундов проведено:" in text

