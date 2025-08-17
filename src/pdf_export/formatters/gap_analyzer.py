# src/pdf_export/formatters/gap_analyzer.py
# --- agent_meta ---
# role: gap-analyzer-pdf-formatter
# owner: @backend
# contract: PDF форматтер для результатов GAP анализа резюме
# last_reviewed: 2025-08-17
# interfaces:
#   - GapAnalyzerPDFFormatter
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime

from .base import AbstractPDFFormatter


class GapAnalyzerPDFFormatter(AbstractPDFFormatter):
    """Форматтер PDF отчета для GAP анализа резюме."""
    
    @property
    def feature_name(self) -> str:
        return "gap_analyzer"
    
    @property
    def template_name(self) -> str:
        return "gap_analyzer.html"
    
    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка контекста для шаблона GAP анализа."""
        
        # Основная информация
        context = {
            "title": "Анализ соответствия резюме требованиям вакансии",
            "generated_at": self._format_datetime(metadata.get("generated_at")),
            "feature_version": metadata.get("version", "v1"),
        }
        
        # Первичный скрининг
        primary_screening = data.get("primary_screening", {})
        context["screening"] = {
            "overall_result": primary_screening.get("overall_screening_result", "НЕТ ДАННЫХ"),
            "job_title_match": primary_screening.get("job_title_match", False),
            "experience_match": primary_screening.get("experience_years_match", False),
            "key_skills_visible": primary_screening.get("key_skills_visible", False),
            "location_suitable": primary_screening.get("location_suitable", False),
            "salary_match": primary_screening.get("salary_expectations_match", False),
            "notes": primary_screening.get("screening_notes", "")
        }
        
        # Анализ требований
        requirements = data.get("requirements_analysis", [])
        context["requirements"] = self._format_requirements(requirements)
        
        # Рекомендации по критичности
        context["critical_recommendations"] = self._format_recommendations(
            data.get("critical_recommendations", []), "CRITICAL"
        )
        context["important_recommendations"] = self._format_recommendations(
            data.get("important_recommendations", []), "IMPORTANT"
        )
        context["optional_recommendations"] = self._format_recommendations(
            data.get("optional_recommendations", []), "DESIRED"
        )
        
        # Оценка качества резюме
        quality = data.get("quality_assessment", {})
        context["quality"] = {
            "structure_clarity": quality.get("structure_clarity", 0),
            "content_relevance": quality.get("content_relevance", 0),
            "achievement_focus": quality.get("achievement_focus", 0),
            "adaptation_quality": quality.get("adaptation_quality", 0),
            "overall_impression": quality.get("overall_impression", "НЕТ ДАННЫХ"),
            "notes": quality.get("quality_notes", "")
        }
        
        # Итоговые результаты
        context["summary"] = {
            "match_percentage": data.get("overall_match_percentage", 0),
            "hiring_recommendation": data.get("hiring_recommendation", "НЕТ"),
            "strengths": data.get("key_strengths", []),
            "gaps": data.get("major_gaps", []),
            "next_steps": data.get("next_steps", [])
        }
        
        return context
    
    def _format_requirements(self, requirements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Форматирование анализа требований для шаблона."""
        formatted = []
        
        for req in requirements:
            formatted.append({
                "text": req.get("requirement_text", ""),
                "type": self._translate_requirement_type(req.get("requirement_type")),
                "category": self._translate_skill_category(req.get("skill_category")),
                "status": self._translate_compliance_status(req.get("compliance_status")),
                "status_class": self._get_status_css_class(req.get("compliance_status")),
                "impact": self._translate_decision_impact(req.get("decision_impact")),
                "impact_class": self._get_impact_css_class(req.get("decision_impact")),
                "evidence": req.get("evidence_in_resume", "Не указано"),
                "gap": req.get("gap_description", ""),
                "rationale": req.get("decision_rationale", "")
            })
        
        return formatted
    
    def _format_recommendations(self, recommendations: List[Dict[str, Any]], level: str) -> List[Dict[str, Any]]:
        """Форматирование рекомендаций для шаблона."""
        formatted = []
        
        for rec in recommendations:
            formatted.append({
                "section": self._translate_section_name(rec.get("section")),
                "issue": rec.get("issue_description", ""),
                "actions": rec.get("specific_actions", []),
                "example": rec.get("example_wording", ""),
                "rationale": rec.get("business_rationale", ""),
                "level": level,
                "level_class": level.lower()
            })
        
        return formatted
    
    def _format_datetime(self, dt_str: str | None) -> str:
        """Форматирование даты для отображения."""
        if not dt_str:
            return datetime.now().strftime("%d.%m.%Y %H:%M")
        
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            return dt_str
    
    def _translate_requirement_type(self, type_val: str | None) -> str:
        """Перевод типа требования."""
        mapping = {
            "MUST_HAVE": "Обязательно",
            "NICE_TO_HAVE": "Желательно", 
            "ADDITIONAL_BONUS": "Дополнительный плюс"
        }
        return mapping.get(type_val or "", type_val or "")
    
    def _translate_skill_category(self, category: str | None) -> str:
        """Перевод категории навыка."""
        mapping = {
            "HARD_SKILLS": "Технические навыки",
            "SOFT_SKILLS": "Личные качества",
            "EXPERIENCE": "Опыт работы",
            "EDUCATION": "Образование"
        }
        return mapping.get(category or "", category or "")
    
    def _translate_compliance_status(self, status: str | None) -> str:
        """Перевод статуса соответствия."""
        mapping = {
            "FULL_MATCH": "Полное соответствие",
            "PARTIAL_MATCH": "Частичное соответствие", 
            "MISSING": "Отсутствует",
            "UNCLEAR": "Неясно"
        }
        return mapping.get(status or "", status or "")
    
    def _translate_decision_impact(self, impact: str | None) -> str:
        """Перевод влияния на решение."""
        mapping = {
            "BLOCKER": "Блокирующий фактор",
            "HIGH": "Высокое влияние",
            "MEDIUM": "Среднее влияние", 
            "LOW": "Низкое влияние"
        }
        return mapping.get(impact or "", impact or "")
    
    def _translate_section_name(self, section: str | None) -> str:
        """Перевод названия раздела резюме."""
        mapping = {
            "title": "Заголовок/Позиция",
            "skills": "Навыки",
            "experience": "Опыт работы",
            "education": "Образование",
            "structure": "Структура резюме",
            "projects": "Проекты",
            "achievements": "Достижения",
            "certificates": "Сертификаты",
            "portfolio": "Портфолио",
            "contacts": "Контактная информация",
            "cover_letter": "Сопроводительное письмо"
        }
        return mapping.get(section or "", section or "")
    
    def _get_status_css_class(self, status: str | None) -> str:
        """CSS класс для статуса соответствия."""
        mapping = {
            "FULL_MATCH": "status-full",
            "PARTIAL_MATCH": "status-partial",
            "MISSING": "status-missing", 
            "UNCLEAR": "status-unclear"
        }
        return mapping.get(status or "", "status-unclear")
    
    def _get_impact_css_class(self, impact: str | None) -> str:
        """CSS класс для влияния на решение."""
        mapping = {
            "BLOCKER": "impact-blocker",
            "HIGH": "impact-high",
            "MEDIUM": "impact-medium",
            "LOW": "impact-low"
        }
        return mapping.get(impact or "", "impact-low")