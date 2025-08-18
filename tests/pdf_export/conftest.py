# tests/pdf_export/conftest.py
# --- agent_meta ---
# role: pdf-export-test-fixtures
# owner: @backend
# contract: Общие фикстуры для тестов PDF экспорта
# last_reviewed: 2025-08-17
# interfaces:
#   - sample_gap_analysis_data()
#   - sample_cover_letter_data()
#   - pdf_service()
# --- /agent_meta ---

from typing import Dict, Any
from datetime import datetime

import pytest

from src.pdf_export.service import PDFExportService
from src.pdf_export.formatters import (
    GapAnalyzerPDFFormatter,
    CoverLetterPDFFormatter,
    InterviewChecklistPDFFormatter,
)


@pytest.fixture
def sample_gap_analysis_data() -> Dict[str, Any]:
    """Образец данных GAP анализа для тестов."""
    return {
        "primary_screening": {
            "job_title_match": True,
            "experience_years_match": True,
            "key_skills_visible": False,
            "location_suitable": True,
            "salary_expectations_match": False,
            "overall_screening_result": "ВОЗМОЖНО",
            "screening_notes": "Ключевые навыки требуют уточнения"
        },
        "requirements_analysis": [
            {
                "requirement_text": "Python 3+ лет опыта",
                "requirement_type": "MUST_HAVE",
                "skill_category": "HARD_SKILLS",
                "compliance_status": "FULL_MATCH",
                "evidence_in_resume": "Python Developer 3 года в Acme Corp",
                "gap_description": None,
                "decision_impact": "HIGH",
                "decision_rationale": "Основной стек технологий"
            },
            {
                "requirement_text": "FastAPI опыт",
                "requirement_type": "NICE_TO_HAVE",
                "skill_category": "HARD_SKILLS",
                "compliance_status": "PARTIAL_MATCH",
                "evidence_in_resume": "REST API разработка",
                "gap_description": "Нет прямого упоминания FastAPI",
                "decision_impact": "MEDIUM",
                "decision_rationale": "Важно для текущих проектов"
            }
        ],
        "quality_assessment": {
            "structure_clarity": 8,
            "content_relevance": 7,
            "achievement_focus": 6,
            "adaptation_quality": 5,
            "overall_impression": "СРЕДНИЙ",
            "quality_notes": "Хорошая структура, но нужно больше метрик"
        },
        "critical_recommendations": [
            {
                "section": "skills",
                "criticality": "CRITICAL",
                "issue_description": "Нет упоминания FastAPI",
                "specific_actions": ["Добавить FastAPI в ключевые навыки", "Привести примеры API проектов"],
                "example_wording": "FastAPI: разработка REST API с высокой производительностью",
                "business_rationale": "Основной фреймворк для новых проектов"
            }
        ],
        "important_recommendations": [],
        "optional_recommendations": [],
        "overall_match_percentage": 75,
        "hiring_recommendation": "ВОЗМОЖНО",
        "key_strengths": ["Опыт Python", "Хорошая структура резюме"],
        "major_gaps": ["FastAPI специфика", "Недостаточно метрик достижений"],
        "next_steps": ["Техническое интервью по FastAPI", "Уточнить опыт с асинхронным программированием"]
    }


@pytest.fixture
def sample_cover_letter_data() -> Dict[str, Any]:
    """Образец данных сопроводительного письма для тестов."""
    return {
        "role_type": "DEVELOPER",
        "company_context": {
            "company_name": "TechCorp",
            "company_size": "MEDIUM",
            "company_culture": "Инновационная культура разработки",
            "product_info": "SaaS платформа для автоматизации бизнес-процессов"
        },
        "estimated_length": "MEDIUM",
        "skills_match": {
            "matched_skills": ["Python", "FastAPI", "PostgreSQL"],
            "relevant_experience": "3 года разработки backend сервисов",
            "quantified_achievement": "Увеличил производительность API на 40%",
            "growth_potential": "Изучение микросервисной архитектуры"
        },
        "personalization": {
            "company_hook": "Привлекает фокус на инновации и качество продукта",
            "role_motivation": "Возможность работать с современным стеком технологий",
            "value_proposition": "Опыт оптимизации производительности и архитектуры"
        },
        "subject_line": "Backend Developer - готов присоединиться к команде TechCorp",
        "personalized_greeting": "Добрый день, команда TechCorp!",
        "opening_hook": "За последний год оптимизировал API, увеличив производительность на 40% в проекте с 1M+ пользователей.",
        "company_interest": "Привлекает ваш подход к построению SaaS решений и фокус на пользовательском опыте.",
        "relevant_experience": "3 года опыта разработки backend на Python/FastAPI, работа с высоконагруженными системами.",
        "value_demonstration": "Могу применить опыт оптимизации для улучшения производительности ваших сервисов и масштабирования.",
        "growth_mindset": "Готов изучать новые технологии в вашем стеке и делиться знаниями с командой.",
        "professional_closing": "Буду рад обсудить, как мой опыт может помочь в развитии ваших продуктов.",
        "signature": "С уважением,\nИван Иванов\nivan@example.com\n+7-XXX-XXX-XXXX",
        "personalization_score": 8,
        "professional_tone_score": 9,
        "relevance_score": 7,
        "improvement_suggestions": [
            "Добавить ссылку на GitHub с примерами кода",
            "Уточнить опыт работы с конкретными технологиями из вакансии"
        ]
    }


@pytest.fixture
def sample_interview_checklist_data() -> Dict[str, Any]:
    """Образец данных интервью-чеклиста для тестов."""
    import json
    from pathlib import Path

    # Берем реалистичный сохраненный результат из tests/data
    data_path = Path("tests/data/interview_checklist_result_6423ab26.json")
    assert data_path.exists(), "Отсутствуют тестовые данные interview_checklist"
    with data_path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Образец метаданных для тестов."""
    return {
        "feature_name": "test_feature",
        "version": "v1",
        "generated_at": datetime.now().isoformat(),
        "source_file": "test_data.json"
    }


@pytest.fixture
def pdf_service() -> PDFExportService:
    """Фикстура PDF сервиса."""
    return PDFExportService()


@pytest.fixture
def gap_analyzer_formatter() -> GapAnalyzerPDFFormatter:
    """Фикстура форматтера GAP анализа."""
    return GapAnalyzerPDFFormatter()


@pytest.fixture
def cover_letter_formatter() -> CoverLetterPDFFormatter:
    """Фикстура форматтера сопроводительного письма."""
    return CoverLetterPDFFormatter()


@pytest.fixture
def interview_checklist_formatter() -> InterviewChecklistPDFFormatter:
    """Фикстура форматтера интервью-чеклиста."""
    return InterviewChecklistPDFFormatter()
