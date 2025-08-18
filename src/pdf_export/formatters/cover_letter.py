# src/pdf_export/formatters/cover_letter.py
# --- agent_meta ---
# role: cover-letter-pdf-formatter
# owner: @backend
# contract: PDF форматтер для сопроводительных писем
# last_reviewed: 2025-08-17
# interfaces:
#   - CoverLetterPDFFormatter
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from .base import AbstractPDFFormatter


class CoverLetterPDFFormatter(AbstractPDFFormatter):
    """Форматтер PDF отчета для сопроводительного письма."""
    
    @property
    def feature_name(self) -> str:
        return "cover_letter"
    
    @property
    def template_name(self) -> str:
        return "cover_letter.html"
    
    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовка контекста для шаблона сопроводительного письма."""
        
        # Основная информация
        context = {
            "title": "Сопроводительное письмо",
            "generated_at": self._format_datetime(metadata.get("generated_at")),
            "feature_version": metadata.get("version", "v1"),
        }
        
        # Мета-информация
        context["role_type"] = self._translate_role_type(data.get("role_type"))
        context["estimated_length"] = self._translate_length(data.get("estimated_length"))
        
        # Контекст компании
        company_context = data.get("company_context", {})
        context["company"] = {
            "name": company_context.get("company_name", "Неизвестная компания"),
            "size": self._translate_company_size(company_context.get("company_size")),
            "culture": company_context.get("company_culture", ""),
            "product": company_context.get("product_info", "")
        }
        
        # Анализ соответствия навыков
        skills_match = data.get("skills_match", {})
        context["skills_analysis"] = {
            "matched_skills": skills_match.get("matched_skills", []),
            "relevant_experience": skills_match.get("relevant_experience", ""),
            "quantified_achievement": skills_match.get("quantified_achievement", ""),
            "growth_potential": skills_match.get("growth_potential", "")
        }
        
        # Стратегия персонализации
        personalization = data.get("personalization", {})
        context["personalization"] = {
            "company_hook": personalization.get("company_hook", ""),
            "role_motivation": personalization.get("role_motivation", ""),
            "value_proposition": personalization.get("value_proposition", "")
        }
        
        # Структура письма
        context["letter"] = {
            "subject_line": data.get("subject_line", ""),
            "greeting": data.get("personalized_greeting", ""),
            "opening_hook": data.get("opening_hook", ""),
            "company_interest": data.get("company_interest", ""),
            "relevant_experience": data.get("relevant_experience", ""),
            "value_demonstration": data.get("value_demonstration", ""),
            "growth_mindset": data.get("growth_mindset", ""),
            "closing": data.get("professional_closing", ""),
            "signature": data.get("signature", "")
        }
        
        # Оценки качества
        context["quality_scores"] = {
            "personalization": data.get("personalization_score", 0),
            "professional_tone": data.get("professional_tone_score", 0),
            "relevance": data.get("relevance_score", 0)
        }
        
        # Рекомендации по улучшению
        context["improvements"] = data.get("improvement_suggestions", [])
        
        return context
    
    def _format_datetime(self, dt_str: str | None) -> str:
        """Форматирование даты для отображения."""
        if not dt_str:
            return datetime.now().strftime("%d.%m.%Y %H:%M")
        
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            return dt_str
    
    def _translate_role_type(self, role_type: str | None) -> str:
        """Перевод типа роли."""
        mapping = {
            "DEVELOPER": "Разработчик",
            "QA_ENGINEER": "QA Инженер",
            "ANALYST": "Аналитик",
            "DEVOPS": "DevOps",
            "DESIGNER": "Дизайнер",
            "MANAGER": "Менеджер",
            "ML_ENGINEER": "ML Инженер",
            "DATA_SCIENTIST": "Data Scientist",
            "OTHER": "Другое"
        }
        return mapping.get(role_type or "", role_type or "Не указано")
    
    def _translate_length(self, length: str | None) -> str:
        """Перевод длины письма."""
        mapping = {
            "SHORT": "Краткое",
            "MEDIUM": "Среднее",
            "LONG": "Развернутое"
        }
        return mapping.get(length or "", length or "Не указано")
    
    def _translate_company_size(self, size: str | None) -> str:
        """Перевод размера компании."""
        mapping = {
            "STARTUP": "Стартап",
            "MEDIUM": "Средняя компания",
            "LARGE": "Крупная компания",
            "ENTERPRISE": "Корпорация"
        }
        return mapping.get(size or "", size or "Не указано")