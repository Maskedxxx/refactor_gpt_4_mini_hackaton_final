# tests/llm_features/test_cover_letter_integration.py
# --- agent_meta ---
# role: llm-features-integration-test
# owner: @backend
# contract: Интеграционный тест полного пайплайна cover_letter через LLM Features Framework
# last_reviewed: 2025-08-15
# interfaces:
#   - test_cover_letter_full_pipeline()
#   - test_cover_letter_via_webapp_api()
# --- /agent_meta ---

import pytest
from unittest.mock import patch, AsyncMock
import json
import os

from src.llm_features.registry import get_global_registry
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_cover_letter.options import CoverLetterOptions
from src.llm_cover_letter.models import EnhancedCoverLetter

# Импортируем фикстуры из webapp  
from tests.webapp.conftest import app_ctx, async_client


@pytest.fixture
def sample_test_data():
    """Загружаем тестовые данные из JSON файлов"""
    test_dir = os.path.join(os.path.dirname(__file__), "../data")
    
    with open(os.path.join(test_dir, "simple_resume.json")) as f:
        resume_data = json.load(f)
        
    with open(os.path.join(test_dir, "simple_vacancy.json")) as f:
        vacancy_data = json.load(f)
    
    return {
        "resume": ResumeInfo(**resume_data),
        "vacancy": VacancyInfo(**vacancy_data)
    }


@pytest.fixture
def mock_llm_response():
    """Мок ответ от LLM для сопроводительного письма"""
    from src.llm_cover_letter.models import (
        RoleType, CompanyContext, SkillsMatchAnalysis, PersonalizationStrategy
    )
    
    return EnhancedCoverLetter(
        role_type=RoleType.DATA_SCIENTIST,
        company_context=CompanyContext(
            company_name="Сбер Банк",
            company_size="LARGE",
            company_culture="Инновации и технологический прогресс",
            product_info="Банковские AI-решения"
        ),
        estimated_length="MEDIUM",
        improvement_suggestions=[
            "Добавить больше конкретных метрик",
            "Упомянуть специфические проекты Сбера"
        ],
        skills_match=SkillsMatchAnalysis(
            matched_skills=["Python", "LLM", "NLP", "LangChain"],
            relevant_experience="Автоматизация HR-процессов и повышение точности поиска на 40%",
            quantified_achievement="Создал LLM-ансамбль, повысивший точность на 40%",
            growth_potential="Готов изучить PyTorch для deep learning задач"
        ),
        personalization=PersonalizationStrategy(
            company_hook="Привлекает лидерство Сбера в AI-инновациях",
            role_motivation="Опыт внедрения production LLM-решений",
            value_proposition="Повышение эффективности AI-систем банка"
        ),
        subject_line="AI Engineer - готов повысить эффективность LLM-решений Сбера",
        personalized_greeting="Уважаемая команда Сбер Банка,",
        opening_hook="Как AI Engineer с 3+ годами опыта создания production LLM-решений, я готов внести значительный вклад в развитие команды Сбер Банка.",
        company_interest="Привлекает лидерство Сбера в финтех инновациях и внедрении AI-решений",
        relevant_experience="Автоматизировал HR-процессы, повысив точность корпоративного поиска на 40% через внедрение LLM-ансамбля",
        value_demonstration="Мой опыт создания production LLM-решений поможет масштабировать AI-инициативы банка",
        growth_mindset="Готов изучить PyTorch для расширения deep learning компетенций",
        professional_closing="Буду рад обсудить, как мой опыт поможет достичь амбициозных целей команды",
        signature="С уважением,\nМаксим Немов\n+7 987 505-69-90\naangers07@gmail.com",
        personalization_score=8,
        professional_tone_score=9,
        relevance_score=8
    )


@pytest.mark.asyncio
async def test_cover_letter_full_pipeline(sample_test_data, mock_llm_response):
    """Тест полного пайплайна генерации сопроводительного письма через FeatureRegistry"""
    
    # Мокаем OpenAI API
    with patch('src.llm_features.base.generator.OpenAI') as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        # Получаем реестр и генератор
        registry = get_global_registry()
        
        # Мокаем вызов LLM, чтобы не тратить деньги и не зависеть от сети
        with patch('src.llm_cover_letter.service.LLMCoverLetterGenerator._call_llm') as mock_llm_call:
            mock_llm_call.return_value = mock_llm_response
            
            # Получаем генератор из реестра
            generator = registry.get_generator("cover_letter", version="v1")
            
            # Опции для генерации
            options = CoverLetterOptions(
                temperature=0.4,
                language="ru", 
                quality_checks=False  # Отключаем проверки для тестирования
            )
            
            # Выполняем генерацию
            result = await generator.generate(
                sample_test_data["resume"],
                sample_test_data["vacancy"], 
                options
            )
            
            # Проверяем что результат является EnhancedCoverLetter
            assert isinstance(result, EnhancedCoverLetter)
            assert result.opening_hook == mock_llm_response.opening_hook
            assert result.company_interest == mock_llm_response.company_interest
            assert "Python" in result.skills_match.matched_skills
            
            # Проверяем что LLM был вызван
            mock_llm_call.assert_called_once()
            
            # Проверяем форматирование для email
            email_text = generator.format_for_email(result)
            assert isinstance(email_text, str)
            assert len(email_text) > 0
            assert "Сбер Банк" in email_text  # Должна быть упомянута компания


@pytest.mark.asyncio
async def test_cover_letter_via_webapp_api(async_client, sample_test_data, mock_llm_response):
    """Тест генерации cover letter через универсальное API webapp"""
    
    # Мокаем OpenAI API
    with patch('src.llm_features.base.generator.OpenAI') as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        # Мокаем вызов LLM в генераторе
        with patch('src.llm_cover_letter.service.LLMCoverLetterGenerator._call_llm') as mock_llm_call:
            mock_llm_call.return_value = mock_llm_response
            
            # Подготавливаем данные запроса
            request_data = {
                "resume": sample_test_data["resume"].model_dump(),
                "vacancy": sample_test_data["vacancy"].model_dump(),
                "options": {
                    "temperature": 0.4,
                    "language": "ru",
                    "quality_checks": False
                }
            }
            
            # Отправляем запрос через универсальное API
            response = await async_client.post(
                "/features/cover_letter/generate",
                json=request_data
            )
            
            # Проверяем успешный ответ
            assert response.status_code == 200
            data = response.json()
            
            # Проверяем структуру ответа
            assert data["feature_name"] == "cover_letter"
            assert "result" in data
            
            # Проверяем что LLM был вызван
            mock_llm_call.assert_called_once()
            
            # Проверяем что в результате есть данные сопроводительного письма
            result_output = data["result"]  # Полная модель EnhancedCoverLetter
            assert "opening_hook" in result_output
            assert "company_interest" in result_output
            assert result_output["opening_hook"] == mock_llm_response.opening_hook
            
            # Проверяем formatted_output если он есть
            if data.get("formatted_output"):
                formatted = data["formatted_output"]
                assert isinstance(formatted, str)
                assert "Сбер Банк" in formatted


@pytest.mark.asyncio  
async def test_cover_letter_registry_integration():
    """Тест интеграции cover_letter с реестром - проверяем что фича автоматически зарегистрирована"""
    
    registry = get_global_registry()
    
    # Проверяем что фича зарегистрирована
    feature_names = registry.get_feature_names()
    assert "cover_letter" in feature_names
    
    # Проверяем версии
    versions = registry.get_versions("cover_letter")
    assert "v1" in versions or "v2" in versions  # может быть любая версия
    
    # Проверяем список всех фич
    features = registry.list_features()
    cover_letter_features = [f for f in features if f.name == "cover_letter"]
    assert len(cover_letter_features) > 0
    
    # Мокаем OpenAI для создания генератора
    with patch('src.llm_features.base.generator.OpenAI') as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        # Проверяем что можем получить генератор
        generator = registry.get_generator("cover_letter")
        assert generator is not None
        assert hasattr(generator, 'generate')
        assert hasattr(generator, 'format_for_email')


@pytest.mark.asyncio
async def test_cover_letter_error_handling(sample_test_data):
    """Тест обработки ошибок в пайплайне cover_letter"""
    
    # Мокаем OpenAI API
    with patch('src.llm_features.base.generator.OpenAI') as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        registry = get_global_registry()
        
        # Мокаем LLM чтобы он вызывал исключение
        with patch('src.llm_cover_letter.service.LLMCoverLetterGenerator._call_llm') as mock_llm_call:
            mock_llm_call.side_effect = Exception("LLM service unavailable")
            
            generator = registry.get_generator("cover_letter")
            options = CoverLetterOptions(quality_checks=False)
            
            # Проверяем что исключение пробрасывается
            with pytest.raises(Exception) as exc_info:
                await generator.generate(
                    sample_test_data["resume"],
                    sample_test_data["vacancy"],
                    options
                )
            
            assert "LLM service unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cover_letter_with_different_versions():
    """Тест работы с разными версиями фичи cover_letter"""
    
    # Мокаем OpenAI API
    with patch('src.llm_features.base.generator.OpenAI') as mock_openai:
        mock_openai.return_value = AsyncMock()
        
        registry = get_global_registry()
        
        # Проверяем что можем получить генератор без указания версии (default)
        default_generator = registry.get_generator("cover_letter")
        assert default_generator is not None
        
        # Проверяем что можем получить конкретную версию
        v1_generator = registry.get_generator("cover_letter", version="v1")
        assert v1_generator is not None
        
        # Проверяем что это тот же класс (пока у нас только v1)
        assert isinstance(default_generator, type(v1_generator))