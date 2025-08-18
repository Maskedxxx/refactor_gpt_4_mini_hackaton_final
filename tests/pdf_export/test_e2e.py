# tests/pdf_export/test_e2e.py
# --- agent_meta ---
# role: pdf-export-e2e-tests
# owner: @backend
# contract: End-to-end тесты полного workflow: генерация фичи → PDF экспорт
# last_reviewed: 2025-08-17
# interfaces:
#   - test_gap_analyzer_full_workflow()
#   - test_cover_letter_full_workflow()
#   - test_webapp_pdf_generation()
# --- /agent_meta ---

import tempfile
import json
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest

from src.llm_features.registry import get_global_registry
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_gap_analyzer.options import GapAnalyzerOptions
from src.llm_cover_letter.options import CoverLetterOptions
from src.pdf_export.service import PDFExportService

# Импортируем фикстуры из webapp для async client
from tests.webapp.conftest import async_client  # noqa: F401


@pytest.fixture
def sample_resume_vacancy_data():
    """Загружаем реальные тестовые данные резюме и вакансии."""
    test_dir = Path("tests/data")
    
    with open(test_dir / "simple_resume.json") as f:
        resume_data = json.load(f)
    
    with open(test_dir / "simple_vacancy.json") as f:
        vacancy_data = json.load(f)
    
    return {
        "resume": ResumeInfo(**resume_data),
        "vacancy": VacancyInfo(**vacancy_data),
    }


@pytest.fixture
def mock_llm_responses():
    """Моки ответов LLM для всех фич."""
    return {
        "gap_analyzer": {
            "primary_screening": {
                "job_title_match": True,
                "experience_years_match": True,
                "key_skills_visible": True,
                "location_suitable": True,
                "salary_expectations_match": False,
                "overall_screening_result": "ПРИНЯТЬ",
                "screening_notes": "Основные требования выполнены",
            },
            "requirements_analysis": [
                {
                    "requirement_text": "Python 3+ лет",
                    "requirement_type": "MUST_HAVE",
                    "skill_category": "HARD_SKILLS",
                    "compliance_status": "FULL_MATCH",
                    "evidence_in_resume": "Python Developer 3 года",
                    "gap_description": None,
                    "decision_impact": "HIGH",
                    "decision_rationale": "Ключевая технология",
                }
            ],
            "quality_assessment": {
                "structure_clarity": 8,
                "content_relevance": 8,
                "achievement_focus": 7,
                "adaptation_quality": 7,
                "overall_impression": "СИЛЬНЫЙ",
                "quality_notes": "Хорошая структура",
            },
            "critical_recommendations": [],
            "important_recommendations": [],
            "optional_recommendations": [],
            "overall_match_percentage": 85,
            "hiring_recommendation": "ДА",
            "key_strengths": ["Сильный Python", "Коммерческий опыт"],
            "major_gaps": [],
            "next_steps": ["Техническое интервью"],
        },
        "cover_letter": {
            "role_type": "DEVELOPER",
            "company_context": {
                "company_name": "TestCorp",
                "company_size": "MEDIUM",
                "company_culture": "Инновационная",
                "product_info": "SaaS платформа",
            },
            "estimated_length": "MEDIUM",
            "skills_match": {
                "matched_skills": ["Python", "FastAPI"],
                "relevant_experience": "3 года backend разработки",
                "quantified_achievement": "Увеличил производительность на 30%",
                "growth_potential": "Изучение DevOps",
            },
            "personalization": {
                "company_hook": "Привлекает фокус на качество",
                "role_motivation": "Работа с современными технологиями",
                "value_proposition": "Опыт оптимизации",
            },
            "subject_line": "Backend Developer - готов к работе",
            "personalized_greeting": "Добрый день!",
            "opening_hook": "Увеличил производительность API на 30%",
            "company_interest": "Привлекает ваш подход к разработке",
            "relevant_experience": "3 года опыта с Python/FastAPI",
            "value_demonstration": "Могу применить опыт оптимизации",
            "growth_mindset": "Готов изучать новые технологии",
            "professional_closing": "Буду рад обсудить сотрудничество",
            "signature": "С уважением,\\nТестовый Кандидат",
            "personalization_score": 8,
            "professional_tone_score": 9,
            "relevance_score": 7,
            "improvement_suggestions": ["Добавить портфолио"],
        },
    }


class TestGapAnalyzerE2E:
    """End-to-end тесты для GAP анализа."""
    
    @pytest.mark.asyncio
    async def test_gap_analyzer_full_workflow(self, sample_resume_vacancy_data, mock_llm_responses):
        """Тест полного workflow: генерация GAP анализа → PDF экспорт."""
        
        # Мокаем LLM вызовы
        with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
            mock_openai.return_value = AsyncMock()
            
            with patch("src.llm_gap_analyzer.service.LLMGapAnalyzerGenerator._call_llm") as mock_llm:
                # Настраиваем мок для возвращения правильного типа
                from src.llm_gap_analyzer.models import EnhancedResumeTailoringAnalysis
                mock_result = EnhancedResumeTailoringAnalysis.model_validate(mock_llm_responses["gap_analyzer"])
                mock_llm.return_value = mock_result
                
                # Шаг 1: Генерируем GAP анализ через registry
                registry = get_global_registry()
                generator = registry.get_generator("gap_analyzer", version="v1")
                
                options = GapAnalyzerOptions(
                    temperature=0.2,
                    language="ru",
                )
                
                gap_result = await generator.generate(
                    sample_resume_vacancy_data["resume"],
                    sample_resume_vacancy_data["vacancy"],
                    options,
                )
                
                # Проверяем результат генерации
                assert gap_result.overall_match_percentage == 85
                assert gap_result.hiring_recommendation == "ДА"
                
                # Шаг 2: Экспортируем в PDF
                pdf_service = PDFExportService()
                metadata = {
                    "feature_name": "gap_analyzer",
                    "version": "v1",
                    "generated_at": "2025-08-17T10:00:00",
                }
                
                pdf_content = await pdf_service.generate_pdf(
                    feature_name="gap_analyzer",
                    data=gap_result.model_dump(),
                    metadata=metadata,
                )
                
                # Проверяем PDF
                assert isinstance(pdf_content, bytes)
                assert len(pdf_content) > 1000
                assert pdf_content.startswith(b"%PDF-")
                
                # Сохраняем для визуальной проверки
                with tempfile.NamedTemporaryFile(suffix="_gap_e2e.pdf", delete=False) as tmp:
                    tmp.write(pdf_content)
                    print(f"\nGAP анализ PDF сохранен: {tmp.name}")


class TestCoverLetterE2E:
    """End-to-end тесты для сопроводительного письма."""
    
    @pytest.mark.asyncio
    async def test_cover_letter_full_workflow(self, sample_resume_vacancy_data, mock_llm_responses):
        """Тест полного workflow: генерация письма → PDF экспорт."""
        
        with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
            mock_openai.return_value = AsyncMock()
            
            with patch("src.llm_cover_letter.service.LLMCoverLetterGenerator._call_llm") as mock_llm:
                # Настраиваем мок для возвращения правильного типа
                from src.llm_cover_letter.models import EnhancedCoverLetter
                mock_result = EnhancedCoverLetter.model_validate(mock_llm_responses["cover_letter"])
                mock_llm.return_value = mock_result
                
                # Шаг 1: Генерируем сопроводительное письмо
                registry = get_global_registry()
                generator = registry.get_generator("cover_letter", version="v1")
                
                options = CoverLetterOptions(
                    temperature=0.3,
                    language="ru",
                )
                
                letter_result = await generator.generate(
                    sample_resume_vacancy_data["resume"],
                    sample_resume_vacancy_data["vacancy"],
                    options,
                )
                
                # Проверяем результат генерации
                assert letter_result.role_type == "DEVELOPER"
                assert letter_result.personalization_score == 8
                
                # Шаг 2: Экспортируем в PDF
                pdf_service = PDFExportService()
                metadata = {
                    "feature_name": "cover_letter",
                    "version": "v1",
                    "generated_at": "2025-08-17T10:00:00",
                }
                
                pdf_content = await pdf_service.generate_pdf(
                    feature_name="cover_letter",
                    data=letter_result.model_dump(),
                    metadata=metadata,
                )
                
                # Проверяем PDF
                assert isinstance(pdf_content, bytes)
                assert len(pdf_content) > 1000
                assert pdf_content.startswith(b"%PDF-")
                
                # Сохраняем для визуальной проверки
                with tempfile.NamedTemporaryFile(suffix="_cover_e2e.pdf", delete=False) as tmp:
                    tmp.write(pdf_content)
                    print(f"\nCover Letter PDF сохранен: {tmp.name}")


class TestWebAppPDFGeneration:
    """End-to-end тесты через веб API."""
    
    @pytest.mark.asyncio
    async def test_webapp_gap_analyzer_pdf_generation(self, async_client, sample_resume_vacancy_data, mock_llm_responses):
        """Тест генерации PDF для GAP анализа через веб API."""
        
        with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
            mock_openai.return_value = AsyncMock()
            
            with patch("src.llm_gap_analyzer.service.LLMGapAnalyzerGenerator._call_llm") as mock_llm:
                from src.llm_gap_analyzer.models import EnhancedResumeTailoringAnalysis
                mock_result = EnhancedResumeTailoringAnalysis.model_validate(mock_llm_responses["gap_analyzer"])
                mock_llm.return_value = mock_result
                
                # Шаг 1: Генерируем через API
                generate_request = {
                    "resume": sample_resume_vacancy_data["resume"].model_dump(),
                    "vacancy": sample_resume_vacancy_data["vacancy"].model_dump(),
                    "options": {
                        "temperature": 0.2,
                        "language": "ru",
                    },
                }
                
                response = await async_client.post(
                    "/features/gap_analyzer/generate",
                    json=generate_request,
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Шаг 2: Генерируем PDF через API
                pdf_request = {
                    "feature_name": "gap_analyzer",
                    "data": data["result"],
                    "metadata": {
                        "feature_name": "gap_analyzer",
                        "version": "v1",
                        "generated_at": "2025-08-17T10:00:00",
                    },
                }
                
                pdf_response = await async_client.post(
                    "/pdf/generate",
                    json=pdf_request,
                )
                
                assert pdf_response.status_code == 200
                assert pdf_response.headers["content-type"] == "application/pdf"
                
                pdf_content = pdf_response.content
                assert len(pdf_content) > 1000
                assert pdf_content.startswith(b"%PDF-")
    
    @pytest.mark.asyncio
    async def test_webapp_cover_letter_pdf_generation(self, async_client, sample_resume_vacancy_data, mock_llm_responses):
        """Тест генерации PDF для сопроводительного письма через веб API."""
        
        with patch("src.llm_features.base.generator.OpenAI") as mock_openai:
            mock_openai.return_value = AsyncMock()
            
            with patch("src.llm_cover_letter.service.LLMCoverLetterGenerator._call_llm") as mock_llm:
                from src.llm_cover_letter.models import EnhancedCoverLetter
                mock_result = EnhancedCoverLetter.model_validate(mock_llm_responses["cover_letter"])
                mock_llm.return_value = mock_result
                
                # Шаг 1: Генерируем через API
                generate_request = {
                    "resume": sample_resume_vacancy_data["resume"].model_dump(),
                    "vacancy": sample_resume_vacancy_data["vacancy"].model_dump(),
                    "options": {
                        "temperature": 0.3,
                        "language": "ru",
                    },
                }
                
                response = await async_client.post(
                    "/features/cover_letter/generate",
                    json=generate_request,
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Шаг 2: Генерируем PDF через API
                pdf_request = {
                    "feature_name": "cover_letter",
                    "data": data["result"],
                    "metadata": {
                        "feature_name": "cover_letter",
                        "version": "v1",
                        "generated_at": "2025-08-17T10:00:00",
                    },
                }
                
                pdf_response = await async_client.post(
                    "/pdf/generate",
                    json=pdf_request,
                )
                
                assert pdf_response.status_code == 200
                assert pdf_response.headers["content-type"] == "application/pdf"
                
                pdf_content = pdf_response.content
                assert len(pdf_content) > 1000
                assert pdf_content.startswith(b"%PDF-")


class TestRealDataWorkflow:
    """Тесты с реальными сохраненными данными."""
    
    @pytest.mark.asyncio
    async def test_load_saved_results_and_generate_pdf(self):
        """Тест загрузки сохраненных результатов и генерации PDF."""
        test_data_dir = Path("tests/data")
        
        # Ищем сохраненные результаты
        gap_files = list(test_data_dir.glob("gap_analysis_result_*.json"))
        cover_files = list(test_data_dir.glob("cover_letter_result_*.json"))
        
        pdf_service = PDFExportService()
        
        # Тестируем GAP анализ результаты
        if gap_files:
            latest_gap_file = max(gap_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_gap_file) as f:
                gap_data = json.load(f)
            
            metadata = {
                "feature_name": "gap_analyzer",
                "version": "v1",
                "generated_at": "2025-08-17T10:00:00",
                "source_file": latest_gap_file.name,
            }
            
            pdf_content = await pdf_service.generate_pdf(
                feature_name="gap_analyzer",
                data=gap_data,
                metadata=metadata,
            )
            
            assert isinstance(pdf_content, bytes)
            assert len(pdf_content) > 1000
            assert pdf_content.startswith(b"%PDF-")
            
            print(f"✓ PDF сгенерирован из {latest_gap_file.name}")
        
        # Тестируем Cover Letter результаты
        if cover_files:
            latest_cover_file = max(cover_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_cover_file) as f:
                cover_data = json.load(f)
            
            metadata = {
                "feature_name": "cover_letter",
                "version": "v1",
                "generated_at": "2025-08-17T10:00:00",
                "source_file": latest_cover_file.name,
            }
            
            pdf_content = await pdf_service.generate_pdf(
                feature_name="cover_letter",
                data=cover_data,
                metadata=metadata,
            )
            
            assert isinstance(pdf_content, bytes)
            assert len(pdf_content) > 1000
            assert pdf_content.startswith(b"%PDF-")
            
            print(f"✓ PDF сгенерирован из {latest_cover_file.name}")
        
        # Если нет сохраненных файлов, тест проходит с предупреждением
        if not gap_files and not cover_files:
            pytest.skip("Нет сохраненных результатов для тестирования. Запустите generate_* скрипты с --save-result")


class TestErrorHandlingE2E:
    """Тесты обработки ошибок в end-to-end сценариях."""
    
    @pytest.mark.asyncio
    async def test_invalid_feature_name_in_workflow(self):
        """Тест обработки некорректного имени фичи."""
        pdf_service = PDFExportService()
        
        with pytest.raises(ValueError, match="Formatter for feature 'invalid_feature' not found"):
            await pdf_service.generate_pdf(
                feature_name="invalid_feature",
                data={},
                metadata={},
            )
    
    @pytest.mark.asyncio
    async def test_corrupted_data_handling(self):
        """Тест обработки поврежденных данных."""
        pdf_service = PDFExportService()
        
        # Пытаемся генерировать PDF с некорректными данными
        with pytest.raises(Exception):  # Может быть KeyError, TypeError и т.д.
            await pdf_service.generate_pdf(
                feature_name="gap_analyzer",
                data={"corrupted": "data"},
                metadata={},
            )