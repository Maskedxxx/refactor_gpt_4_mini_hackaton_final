# src/pdf_export/formatters/interview_checklist.py
# --- agent_meta ---
# role: pdf-formatter-interview-checklist
# owner: @backend
# contract: Форматтер для генерации PDF отчета по результатам фичи llm_interview_checklist
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewChecklistPDFFormatter
# --- /agent_meta ---

from typing import Any, Dict, List, Callable

from src.llm_interview_checklist.models import ProfessionalInterviewChecklist
from src.pdf_export.formatters.base import AbstractPDFFormatter


class InterviewChecklistPDFFormatter(AbstractPDFFormatter):
    """Форматтер для генерации PDF отчета по чек-листу для интервью."""

    @property
    def feature_name(self) -> str:
        return "interview_checklist"

    @property
    def template_name(self) -> str:
        return "interview_checklist.html"

    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает контекст для рендеринга шаблона чек-листа.

        Формирует локализованные подписи, агрегаты и хелперы по аналогии с другими форматтерами
        (gap_analyzer, cover_letter), чтобы шаблон оставался декларативным.
        """
        checklist = ProfessionalInterviewChecklist.model_validate(data)

        # Метаданные
        generated_at = metadata.get("generated_at")
        feature_version = metadata.get("version")

        # Локализация персонализации
        personalization = {
            "candidate_level": self._t_level(checklist.personalization_context.candidate_level.value),
            "vacancy_type": self._t_vacancy_type(checklist.personalization_context.vacancy_type.value),
            "company_format": self._t_company_format(checklist.personalization_context.company_format.value),
            "key_gaps_identified": list(checklist.personalization_context.key_gaps_identified),
            "candidate_strengths": list(checklist.personalization_context.candidate_strengths),
            "critical_focus_areas": list(checklist.personalization_context.critical_focus_areas),
        }

        # Время подготовки
        time_estimates = getattr(checklist, "time_estimates", None)
        time_panel = None
        if time_estimates is not None:
            time_panel = {
                "total": time_estimates.total_time_needed,
                "critical": time_estimates.critical_tasks_time,
                "important": time_estimates.important_tasks_time,
                "optional": time_estimates.optional_tasks_time,
                "daily": time_estimates.daily_schedule_suggestion,
            }

        # Агрегаты по задачам (счётчики по приоритету для технических и доп. действий)
        def _count_by_priority(items: List[Any], priority_field: str) -> Dict[str, int]:
            counters = {"КРИТИЧНО": 0, "ВАЖНО": 0, "ЖЕЛАТЕЛЬНО": 0}
            for it in items:
                val = getattr(it, priority_field, None)
                if val:
                    counters[val.value] = counters.get(val.value, 0) + 1
            return counters

        tech_priority_counters = _count_by_priority(getattr(checklist, "technical_preparation", []), "priority")
        addact_priority_counters = _count_by_priority(getattr(checklist, "additional_actions", []), "urgency")

        # Группировка Technical по категориям
        tech_by_category: Dict[str, List[Any]] = {}
        for item in getattr(checklist, "technical_preparation", []):
            tech_by_category.setdefault(item.category, []).append(item)

        context: Dict[str, Any] = {
            "title": f"Чек-лист подготовки к интервью: {checklist.position_title}",
            "generated_at": generated_at,
            "feature_version": feature_version,
            "company_name": checklist.company_name,

            # Ключевые разделы
            "executive_summary": getattr(checklist, "executive_summary", None),
            "preparation_strategy": getattr(checklist, "preparation_strategy", None),
            "personalization": personalization,
            "time_panel": time_panel,

            # Основные блоки
            "technical_preparation": list(getattr(checklist, "technical_preparation", [])),
            "technical_by_category": tech_by_category,
            "behavioral_preparation": list(getattr(checklist, "behavioral_preparation", [])),
            "company_research": list(getattr(checklist, "company_research", [])),
            "technical_stack_study": list(getattr(checklist, "technical_stack_study", [])),
            "practical_exercises": list(getattr(checklist, "practical_exercises", [])),
            "interview_setup": list(getattr(checklist, "interview_setup", [])),
            "additional_actions": list(getattr(checklist, "additional_actions", [])),

            # Итоговые секции
            "critical_success_factors": list(getattr(checklist, "critical_success_factors", []) or []),
            "common_mistakes_to_avoid": list(getattr(checklist, "common_mistakes_to_avoid", []) or []),
            "last_minute_checklist": list(getattr(checklist, "last_minute_checklist", []) or []),
            "motivation_boost": getattr(checklist, "motivation_boost", None),

            # Агрегаты
            "tech_priority_counters": tech_priority_counters,
            "addact_priority_counters": addact_priority_counters,

            # Хелперы в шаблон
            "get_priority_class": self._get_priority_css_class,
            "get_difficulty_class": self._get_difficulty_css_class,
            "t_priority": self._t_priority,
            "t_level": self._t_level,
            "t_vacancy_type": self._t_vacancy_type,
            "t_company_format": self._t_company_format,
        }
        return context

    def _get_priority_css_class(self, priority: str) -> str:
        """Возвращает CSS-класс в зависимости от приоритета."""
        return {
            "КРИТИЧНО": "priority-critical",
            "ВАЖНО": "priority-important",
            "ЖЕЛАТЕЛЬНО": "priority-desired",
        }.get(priority, "priority-default")

    def _get_difficulty_css_class(self, difficulty: str | None) -> str:
        mapping = {
            "базовый": "difficulty-basic",
            "средний": "difficulty-medium",
            "продвинутый": "difficulty-advanced",
        }
        return mapping.get((difficulty or "").lower(), "difficulty-unknown")

    # === Локализация enum-значений ===
    def _t_priority(self, value: str | None) -> str:
        return value or "N/A"

    def _t_level(self, value: str | None) -> str:
        mapping = {
            "JUNIOR": "Джуниор",
            "MIDDLE": "Миддл",
            "SENIOR": "Сеньор",
            "LEAD": "Лид",
        }
        return mapping.get(value or "", value or "")

    def _t_vacancy_type(self, value: str | None) -> str:
        mapping = {
            "DEVELOPER": "Разработчик",
            "QA_ENGINEER": "Инженер по тестированию",
            "DATA_SPECIALIST": "Специалист по данным",
            "BUSINESS_ANALYST": "Бизнес/Системный аналитик",
            "DESIGNER": "Дизайнер",
            "DEVOPS": "DevOps/SRE",
            "MANAGER": "Менеджер",
            "OTHER": "Другое",
        }
        return mapping.get(value or "", value or "")

    def _t_company_format(self, value: str | None) -> str:
        mapping = {
            "STARTUP": "Стартап",
            "MEDIUM_COMPANY": "Средняя компания",
            "LARGE_CORP": "Крупная корпорация",
            "INTERNATIONAL": "Международная компания",
        }
        return mapping.get(value or "", value or "")
