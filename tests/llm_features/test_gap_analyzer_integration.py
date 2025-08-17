# tests/llm_features/test_gap_analyzer_integration.py
# --- agent_meta ---
# role: llm-gap-analyzer-integration-test
# owner: @backend
# contract: Интеграционные тесты фичи gap_analyzer через FeatureRegistry и универсальное API
# last_reviewed: 2025-08-17
# interfaces:
#   - test_gap_analyzer_full_pipeline()
#   - test_gap_analyzer_via_webapp_api()
#   - test_gap_analyzer_registry_integration()
# --- /agent_meta ---

import os
import json
from unittest.mock import patch, AsyncMock

import pytest

from src.llm_features.registry import get_global_registry
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_gap_analyzer.options import GapAnalyzerOptions
from src.models.gap_analysis_models import (
    EnhancedResumeTailoringAnalysis,
    PrimaryScreeningResult,
    RequirementAnalysis,
    ResumeQualityAssessment,
    DetailedRecommendation,
    RequirementType,
    SkillCategory,
    ComplianceStatus,
    DecisionImpact,
    SectionName,
)

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
def mock_gap_response() -> EnhancedResumeTailoringAnalysis:
    """Формируем валидный мок результата GAP-анализа (строго по модели)."""
    return EnhancedResumeTailoringAnalysis(
        primary_screening=PrimaryScreeningResult(
            job_title_match=True,
            experience_years_match=True,
            key_skills_visible=True,
            location_suitable=True,
            salary_expectations_match=False,
            overall_screening_result="ПРИНЯТЬ",
            screening_notes="Оклад не указан в резюме; остальное ок",
        ),
        requirements_analysis=[
            RequirementAnalysis(
                requirement_text="Python",
                requirement_type=RequirementType.MUST_HAVE,
                skill_category=SkillCategory.HARD_SKILLS,
                compliance_status=ComplianceStatus.FULL_MATCH,
                evidence_in_resume="Опыт 3+ лет коммерческого Python",
                gap_description=None,
                decision_impact=DecisionImpact.HIGH,
                decision_rationale="Ключевая технология для роли",
            ),
            RequirementAnalysis(
                requirement_text="FastAPI",
                requirement_type=RequirementType.MUST_HAVE,
                skill_category=SkillCategory.HARD_SKILLS,
                compliance_status=ComplianceStatus.PARTIAL_MATCH,
                evidence_in_resume="Проекты с REST API, базовый опыт FastAPI",
                gap_description="Мало примеров high-load/async tuning",
                decision_impact=DecisionImpact.MEDIUM,
                decision_rationale="Фреймворк ключевой, но навык доращиваемый",
            ),
        ],
        quality_assessment=ResumeQualityAssessment(
            structure_clarity=8,
            content_relevance=8,
            achievement_focus=7,
            adaptation_quality=6,
            overall_impression="СИЛЬНЫЙ",
            quality_notes="Четкая структура, добавить количественные метрики",
        ),
        critical_recommendations=[
            DetailedRecommendation(
                section=SectionName.ACHIEVEMENTS,
                criticality="CRITICAL",
                issue_description="Мало количественных метрик влияния",
                specific_actions=[
                    "Добавить измеримые KPI по проектам (время ответа, нагрузка)",
                ],
                example_wording="Снизил p95 ответа API с 450мс до 280мс (−38%)",
                business_rationale="Метрики повышают доверие к влиянию кандидата",
            )
        ],
        important_recommendations=[],
        optional_recommendations=[],
        overall_match_percentage=82,
        hiring_recommendation="ДА",
        key_strengths=["Сильный Python", "Коммерческий опыт REST API"],
        major_gaps=["Нетривиальные кейсы оптимизации FastAPI"],
        next_steps=["Проверить опыт асинхронных оптимизаций на интервью"],
    )


@pytest.mark.asyncio
async def test_gap_analyzer_full_pipeline(sample_test_data, mock_gap_response):
    """Тест полного пайплайна генерации GAP-анализа через FeatureRegistry."""

    # Мокаем OpenAI SDK создание клиента
    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()

        # Мокаем сам LLM вызов внутри генератора
        with patch("src.llm_gap_analyzer.service.LLMGapAnalyzerGenerator._call_llm") as mock_llm_call:
            mock_llm_call.return_value = mock_gap_response

            # Получаем генератор через глобальный реестр
            registry = get_global_registry()
            generator = registry.get_generator("gap_analyzer", version="v1")

            # Опции генерации (минимальные)
            options = GapAnalyzerOptions(
                temperature=0.2,
                language="ru",
                include_skill_match_summary=True,
            )

            result = await generator.generate(
                sample_test_data["resume"],
                sample_test_data["vacancy"],
                options,
            )

            # Проверяем тип и ключевые поля результата
            assert isinstance(result, EnhancedResumeTailoringAnalysis)
            assert result.overall_match_percentage == 82
            assert result.hiring_recommendation == "ДА"
            assert result.requirements_analysis[0].requirement_type == RequirementType.MUST_HAVE
            assert result.quality_assessment.structure_clarity >= 1

            # Убедимся, что LLM был вызван
            mock_llm_call.assert_called_once()


@pytest.mark.asyncio
async def test_gap_analyzer_via_webapp_api(async_client, sample_test_data, mock_gap_response):
    """Тест генерации GAP-анализа через универсальное API webapp."""

    # Мокаем OpenAI SDK и генерацию
    with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
        mock_openai.return_value = AsyncMock()

        with patch("src.llm_gap_analyzer.service.LLMGapAnalyzerGenerator._call_llm") as mock_llm_call:
            mock_llm_call.return_value = mock_gap_response

            # Формируем запрос
            request_data = {
                "resume": sample_test_data["resume"].model_dump(),
                "vacancy": sample_test_data["vacancy"].model_dump(),
                "options": {
                    "temperature": 0.2,
                    "language": "ru",
                    "include_skill_match_summary": True,
                },
            }

            response = await async_client.post(
                "/features/gap_analyzer/generate",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()

            assert data["feature_name"] == "gap_analyzer"
            assert data["version"] in ("v1", "default")
            assert "result" in data
            result = data["result"]

            # Проверяем ключевые поля результата от mock'а
            assert result["overall_match_percentage"] == 82
            assert result["hiring_recommendation"] == "ДА"
            assert isinstance(result.get("requirements_analysis"), list)

            # formatted_output может отсутствовать или быть строкой
            if data.get("formatted_output") is not None:
                assert isinstance(data["formatted_output"], str)


@pytest.mark.asyncio
async def test_gap_analyzer_registry_integration():
    """Проверяем, что фича gap_analyzer автоматически зарегистрирована в реестре."""
    registry = get_global_registry()
    feature_names = registry.get_feature_names()
    assert "gap_analyzer" in feature_names

