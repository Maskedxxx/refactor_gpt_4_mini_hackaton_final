# tests/pdf_export/test_formatters.py
# --- agent_meta ---
# role: pdf-formatters-unit-tests
# owner: @backend
# contract: Unit тесты для PDF форматтеров (GapAnalyzer, CoverLetter)
# last_reviewed: 2025-08-17
# interfaces:
#   - test_gap_analyzer_formatter_*()
#   - test_cover_letter_formatter_*()
# --- /agent_meta ---

from typing import Dict, Any

import pytest

from src.pdf_export.formatters import (
    GapAnalyzerPDFFormatter,
    CoverLetterPDFFormatter,
    InterviewChecklistPDFFormatter,
)


class TestGapAnalyzerPDFFormatter:
    """Unit тесты для GAP анализа PDF форматтера."""
    
    def test_feature_name(self, gap_analyzer_formatter):
        assert gap_analyzer_formatter.feature_name == "gap_analyzer"
    
    def test_template_name(self, gap_analyzer_formatter):
        assert gap_analyzer_formatter.template_name == "gap_analyzer.html"
    
    def test_prepare_context_basic_structure(self, gap_analyzer_formatter, sample_gap_analysis_data, sample_metadata):
        """Тест базовой структуры контекста."""
        context = gap_analyzer_formatter.prepare_context(sample_gap_analysis_data, sample_metadata)
        
        # Проверяем обязательные ключи
        required_keys = [
            "title", "generated_at", "feature_version",
            "screening", "requirements", "quality", "summary",
            "critical_recommendations", "important_recommendations", "optional_recommendations"
        ]
        for key in required_keys:
            assert key in context, f"Отсутствует обязательный ключ: {key}"
    
    def test_screening_context_formatting(self, gap_analyzer_formatter, sample_gap_analysis_data, sample_metadata):
        """Тест форматирования секции скрининга."""
        context = gap_analyzer_formatter.prepare_context(sample_gap_analysis_data, sample_metadata)
        
        screening = context["screening"]
        assert screening["overall_result"] == "ВОЗМОЖНО"
        assert screening["job_title_match"] is True
        assert screening["key_skills_visible"] is False
        assert screening["notes"] == "Ключевые навыки требуют уточнения"
    
    def test_requirements_formatting(self, gap_analyzer_formatter, sample_gap_analysis_data, sample_metadata):
        """Тест форматирования анализа требований."""
        context = gap_analyzer_formatter.prepare_context(sample_gap_analysis_data, sample_metadata)
        
        requirements = context["requirements"]
        assert len(requirements) == 2
        
        # Первое требование
        req1 = requirements[0]
        assert req1["text"] == "Python 3+ лет опыта"
        assert req1["type"] == "Обязательно"
        assert req1["category"] == "Технические навыки"
        assert req1["status"] == "Полное соответствие"
        assert req1["status_class"] == "status-full"
        assert req1["impact"] == "Высокое влияние"
        assert req1["impact_class"] == "impact-high"
        
        # Второе требование
        req2 = requirements[1]
        assert req2["status"] == "Частичное соответствие"
        assert req2["status_class"] == "status-partial"
        assert req2["gap"] == "Нет прямого упоминания FastAPI"
    
    def test_quality_assessment_formatting(self, gap_analyzer_formatter, sample_gap_analysis_data, sample_metadata):
        """Тест форматирования оценки качества."""
        context = gap_analyzer_formatter.prepare_context(sample_gap_analysis_data, sample_metadata)
        
        quality = context["quality"]
        assert quality["structure_clarity"] == 8
        assert quality["content_relevance"] == 7
        assert quality["achievement_focus"] == 6
        assert quality["adaptation_quality"] == 5
        assert quality["overall_impression"] == "СРЕДНИЙ"
        assert quality["notes"] == "Хорошая структура, но нужно больше метрик"
    
    def test_recommendations_formatting(self, gap_analyzer_formatter, sample_gap_analysis_data, sample_metadata):
        """Тест форматирования рекомендаций."""
        context = gap_analyzer_formatter.prepare_context(sample_gap_analysis_data, sample_metadata)
        
        critical = context["critical_recommendations"]
        assert len(critical) == 1
        
        rec = critical[0]
        assert rec["section"] == "Навыки"
        assert rec["issue"] == "Нет упоминания FastAPI"
        assert len(rec["actions"]) == 2
        assert rec["actions"][0] == "Добавить FastAPI в ключевые навыки"
        assert rec["level"] == "CRITICAL"
        assert rec["level_class"] == "critical"
    
    def test_summary_formatting(self, gap_analyzer_formatter, sample_gap_analysis_data, sample_metadata):
        """Тест форматирования итоговой сводки."""
        context = gap_analyzer_formatter.prepare_context(sample_gap_analysis_data, sample_metadata)
        
        summary = context["summary"]
        assert summary["match_percentage"] == 75
        assert summary["hiring_recommendation"] == "ВОЗМОЖНО"
        assert len(summary["strengths"]) == 2
        assert len(summary["gaps"]) == 2
        assert len(summary["next_steps"]) == 2
    
    def test_translation_methods(self, gap_analyzer_formatter):
        """Тест методов перевода."""
        # Тест типов требований
        assert gap_analyzer_formatter._translate_requirement_type("MUST_HAVE") == "Обязательно"
        assert gap_analyzer_formatter._translate_requirement_type("NICE_TO_HAVE") == "Желательно"
        assert gap_analyzer_formatter._translate_requirement_type(None) == ""
        
        # Тест категорий навыков
        assert gap_analyzer_formatter._translate_skill_category("HARD_SKILLS") == "Технические навыки"
        assert gap_analyzer_formatter._translate_skill_category("SOFT_SKILLS") == "Личные качества"
        
        # Тест статусов соответствия
        assert gap_analyzer_formatter._translate_compliance_status("FULL_MATCH") == "Полное соответствие"
        assert gap_analyzer_formatter._translate_compliance_status("MISSING") == "Отсутствует"
        
        # Тест CSS классов
        assert gap_analyzer_formatter._get_status_css_class("FULL_MATCH") == "status-full"
        assert gap_analyzer_formatter._get_impact_css_class("HIGH") == "impact-high"


class TestCoverLetterPDFFormatter:
    """Unit тесты для сопроводительного письма PDF форматтера."""
    
    def test_feature_name(self, cover_letter_formatter):
        assert cover_letter_formatter.feature_name == "cover_letter"
    
    def test_template_name(self, cover_letter_formatter):
        assert cover_letter_formatter.template_name == "cover_letter.html"
    
    def test_prepare_context_basic_structure(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест базовой структуры контекста."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        # Проверяем обязательные ключи
        required_keys = [
            "title", "generated_at", "feature_version",
            "role_type", "estimated_length", "company",
            "skills_analysis", "personalization", "letter", 
            "quality_scores", "improvements"
        ]
        for key in required_keys:
            assert key in context, f"Отсутствует обязательный ключ: {key}"
    
    def test_meta_information_formatting(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест форматирования мета-информации."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        assert context["role_type"] == "Разработчик"
        assert context["estimated_length"] == "Среднее"
        
        company = context["company"]
        assert company["name"] == "TechCorp"
        assert company["size"] == "Средняя компания"
        assert company["culture"] == "Инновационная культура разработки"
        assert company["product"] == "SaaS платформа для автоматизации бизнес-процессов"
    
    def test_skills_analysis_formatting(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест форматирования анализа навыков."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        skills = context["skills_analysis"]
        assert skills["matched_skills"] == ["Python", "FastAPI", "PostgreSQL"]
        assert skills["relevant_experience"] == "3 года разработки backend сервисов"
        assert skills["quantified_achievement"] == "Увеличил производительность API на 40%"
        assert skills["growth_potential"] == "Изучение микросервисной архитектуры"
    
    def test_personalization_formatting(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест форматирования стратегии персонализации."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        personalization = context["personalization"]
        assert personalization["company_hook"] == "Привлекает фокус на инновации и качество продукта"
        assert personalization["role_motivation"] == "Возможность работать с современным стеком технологий"
        assert personalization["value_proposition"] == "Опыт оптимизации производительности и архитектуры"
    
    def test_letter_structure_formatting(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест форматирования структуры письма."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        letter = context["letter"]
        assert letter["subject_line"] == "Backend Developer - готов присоединиться к команде TechCorp"
        assert letter["greeting"] == "Добрый день, команда TechCorp!"
        assert "40%" in letter["opening_hook"]
        assert "SaaS решений" in letter["company_interest"]
        assert "Python/FastAPI" in letter["relevant_experience"]
        assert letter["signature"].startswith("С уважением,")
    
    def test_quality_scores_formatting(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест форматирования оценок качества."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        scores = context["quality_scores"]
        assert scores["personalization"] == 8
        assert scores["professional_tone"] == 9
        assert scores["relevance"] == 7
    
    def test_improvements_formatting(self, cover_letter_formatter, sample_cover_letter_data, sample_metadata):
        """Тест форматирования рекомендаций по улучшению."""
        context = cover_letter_formatter.prepare_context(sample_cover_letter_data, sample_metadata)
        
        improvements = context["improvements"]
        assert len(improvements) == 2
        assert "GitHub" in improvements[0]
        assert "технологиями" in improvements[1]
    
    def test_translation_methods(self, cover_letter_formatter):
        """Тест методов перевода."""
        # Тест типов ролей
        assert cover_letter_formatter._translate_role_type("DEVELOPER") == "Разработчик"
        assert cover_letter_formatter._translate_role_type("QA_ENGINEER") == "QA Инженер"
        assert cover_letter_formatter._translate_role_type(None) == "Не указано"
        
        # Тест длины письма
        assert cover_letter_formatter._translate_length("SHORT") == "Краткое"
        assert cover_letter_formatter._translate_length("LONG") == "Развернутое"
        
        # Тест размера компании
        assert cover_letter_formatter._translate_company_size("STARTUP") == "Стартап"
        assert cover_letter_formatter._translate_company_size("ENTERPRISE") == "Корпорация"
    
    def test_datetime_formatting(self, cover_letter_formatter):
        """Тест форматирования даты."""
        # Тест с ISO форматом
        iso_date = "2025-08-17T14:30:00"
        formatted = cover_letter_formatter._format_datetime(iso_date)
        assert "17.08.2025" in formatted
        assert "14:30" in formatted
        
        # Тест с None
        formatted_none = cover_letter_formatter._format_datetime(None)
        assert "." in formatted_none  # Должна быть текущая дата
        
        # Тест с некорректным форматом
        bad_date = "invalid-date"
        formatted_bad = cover_letter_formatter._format_datetime(bad_date)
        assert formatted_bad == "invalid-date"


class TestInterviewChecklistPDFFormatter:
    """Unit тесты для форматтера интервью-чеклиста."""

    def test_feature_and_template_names(self, interview_checklist_formatter):
        assert interview_checklist_formatter.feature_name == "interview_checklist"
        assert interview_checklist_formatter.template_name == "interview_checklist.html"

    def test_prepare_context_basic_structure(
        self,
        interview_checklist_formatter: InterviewChecklistPDFFormatter,
        sample_interview_checklist_data,
        sample_metadata,
    ):
        context = interview_checklist_formatter.prepare_context(
            sample_interview_checklist_data, sample_metadata
        )

        required_keys = [
            "title",
            "generated_at",
            "feature_version",
            "company_name",
            "personalization",
            "time_panel",
            "technical_preparation",
            "behavioral_preparation",
            "company_research",
            "technical_stack_study",
            "practical_exercises",
            "interview_setup",
            "additional_actions",
            "critical_success_factors",
            "common_mistakes_to_avoid",
            "last_minute_checklist",
        ]
        for key in required_keys:
            assert key in context, f"Отсутствует обязательный ключ: {key}"

        # Проверим локализацию персонализации
        pers = context["personalization"]
        assert isinstance(pers["candidate_level"], str)
        assert isinstance(pers["vacancy_type"], str)
        assert isinstance(pers["company_format"], str)

        # Проверим агрегаты и хелперы присутствуют
        assert "tech_priority_counters" in context
        assert callable(context["get_priority_class"])  # хелпер доступен в шаблон

    def test_helpers_and_translations(self, interview_checklist_formatter):
        f = interview_checklist_formatter

        # CSS классы для приоритета
        assert f._get_priority_css_class("КРИТИЧНО") == "priority-critical"
        assert f._get_priority_css_class("ВАЖНО") == "priority-important"
        assert f._get_priority_css_class("ЖЕЛАТЕЛЬНО") == "priority-desired"
        assert f._get_priority_css_class("UNKNOWN") == "priority-default"

        # CSS классы для сложности
        assert f._get_difficulty_css_class("базовый") == "difficulty-basic"
        assert f._get_difficulty_css_class("средний") == "difficulty-medium"
        assert f._get_difficulty_css_class("продвинутый") == "difficulty-advanced"
        assert f._get_difficulty_css_class(None) == "difficulty-unknown"

        # Переводы enum'ов
        assert f._t_level("JUNIOR") == "Джуниор"
        assert f._t_level("LEAD") == "Лид"
        assert f._t_vacancy_type("DEVOPS") == "DevOps/SRE"
        assert f._t_company_format("INTERNATIONAL") == "Международная компания"
