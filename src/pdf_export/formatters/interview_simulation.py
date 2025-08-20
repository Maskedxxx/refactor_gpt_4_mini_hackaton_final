# src/pdf_export/formatters/interview_simulation.py
# --- agent_meta ---
# role: pdf-formatter-interview-simulation
# owner: @backend
# contract: Форматтер для генерации PDF отчета по результатам фичи llm_interview_simulation
# last_reviewed: 2025-08-20
# interfaces:
#   - InterviewSimulationPDFFormatter
# --- /agent_meta ---

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.llm_interview_simulation.models import InterviewSimulation, CandidateLevel, ITRole, QuestionType
from src.pdf_export.formatters.base import AbstractPDFFormatter


class InterviewSimulationPDFFormatter(AbstractPDFFormatter):
    """Форматтер для генерации PDF отчета по симуляции интервью."""

    @property
    def feature_name(self) -> str:
        return "interview_simulation"

    @property
    def template_name(self) -> str:
        return "interview_simulation.html"

    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Подготавливает контекст для рендеринга шаблона симуляции интервью.
        
        Формирует структурированные данные для HTML шаблона с локализацией,
        группировкой диалога по раундам и статистикой интервью.
        """
        simulation = InterviewSimulation.model_validate(data)
        
        # Метаданные
        generated_at = metadata.get("generated_at", datetime.now().isoformat())
        feature_version = metadata.get("version", "v1.1")
        
        # Локализованная информация о кандидате
        candidate_info = {
            "name": simulation.candidate_name,
            "level": self._localize_level(simulation.candidate_profile.detected_level),
            "role": self._localize_role(simulation.candidate_profile.detected_role),
            "experience_years": simulation.candidate_profile.years_of_experience,
            "key_technologies": list(simulation.candidate_profile.key_technologies),
            "management_experience": simulation.candidate_profile.management_experience,
            "education_level": simulation.candidate_profile.education_level,
            "previous_companies": list(simulation.candidate_profile.previous_companies)
        }
        
        # Конфигурация интервью
        interview_config = {
            "target_rounds": simulation.interview_config.target_rounds,
            "focus_areas": [area.value for area in simulation.interview_config.focus_areas],
            "focus_areas_localized": [self._localize_competency_area(area.value) for area in simulation.interview_config.focus_areas],
            "include_behavioral": simulation.interview_config.include_behavioral,
            "include_technical": simulation.interview_config.include_technical,
            "difficulty_level": simulation.interview_config.difficulty_level
        }
        
        # Группировка диалога по раундам
        dialog_by_rounds = self._group_dialog_by_rounds(simulation.dialog_messages)
        
        # Статистика интервью
        interview_stats = self._calculate_interview_stats(simulation)
        
        # Покрытие типов вопросов
        question_coverage = self._analyze_question_coverage(simulation)
        
        # Форматированное время
        try:
            generated_datetime = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
            formatted_date = generated_datetime.strftime("%d.%m.%Y %H:%M")
        except:
            formatted_date = generated_at
        
        context = {
            "title": f"Симуляция интервью: {simulation.position_title}",
            "generated_at": formatted_date,
            "feature_version": feature_version,
            
            # Основная информация
            "position_title": simulation.position_title,
            "company_context": simulation.company_context,
            "candidate_info": candidate_info,
            "interview_config": interview_config,
            
            # Диалог и статистика
            "dialog_by_rounds": dialog_by_rounds,
            "interview_stats": interview_stats,
            "question_coverage": question_coverage,
            
            # Метаданные
            "simulation_metadata": dict(simulation.simulation_metadata),
            
            # Хелперы для шаблона
            "total_rounds_completed": simulation.total_rounds_completed,
            "total_messages": len(simulation.dialog_messages),
        }
        
        return context
    
    def _localize_level(self, level: CandidateLevel) -> str:
        """Локализация уровня кандидата."""
        level_map = {
            "junior": "Junior",
            "middle": "Middle", 
            "senior": "Senior",
            "lead": "Team Lead",
            "unknown": "Неопределен"
        }
        return level_map.get(level.value, level.value.title())
    
    def _localize_role(self, role: ITRole) -> str:
        """Локализация IT-роли."""
        role_map = {
            "developer": "Разработчик",
            "qa": "QA Engineer",
            "devops": "DevOps Engineer", 
            "analyst": "Системный аналитик",
            "project_manager": "Project Manager",
            "designer": "UX/UI Designer",
            "data_scientist": "Data Scientist",
            "system_admin": "Системный администратор",
            "other": "Другое"
        }
        return role_map.get(role.value, role.value.replace('_', ' ').title())
    
    def _localize_question_type(self, question_type: str) -> str:
        """Локализация типов вопросов."""
        type_map = {
            "introduction": "Знакомство",
            "technical_skills": "Технические навыки", 
            "experience": "Опыт работы",
            "behavioral": "Поведенческие вопросы",
            "problem_solving": "Решение проблем",
            "motivation": "Мотивация",
            "culture_fit": "Культурное соответствие",
            "leadership": "Лидерские качества",
            "final": "Завершающие вопросы"
        }
        return type_map.get(question_type, question_type.replace('_', ' ').title())
    
    def _localize_competency_area(self, area: str) -> str:
        """Локализация областей компетенций."""
        area_map = {
            "technical_expertise": "Техническая экспертиза",
            "problem_solving": "Решение проблем",
            "communication": "Коммуникация",
            "teamwork": "Работа в команде",
            "adaptability": "Адаптивность", 
            "leadership": "Лидерство",
            "learning_ability": "Способность к обучению",
            "motivation": "Мотивация",
            "cultural_fit": "Культурное соответствие"
        }
        return area_map.get(area, area.replace('_', ' ').title())
    
    def _group_dialog_by_rounds(self, messages) -> Dict[int, List[Dict[str, Any]]]:
        """Группировка диалога по раундам."""
        dialog_by_rounds = {}
        
        for msg in messages:
            round_num = msg.round_number
            if round_num not in dialog_by_rounds:
                dialog_by_rounds[round_num] = []
            
            message_data = {
                "speaker": msg.speaker,
                "message": msg.message,
                "question_type": self._localize_question_type(msg.question_type.value) if msg.question_type else None,
                "question_type_raw": msg.question_type.value if msg.question_type else None,
                "key_points": list(msg.key_points),
                "timestamp": msg.timestamp,
                "is_hr": msg.speaker == "HR",
                "is_candidate": msg.speaker == "Candidate"
            }
            
            dialog_by_rounds[round_num].append(message_data)
        
        return dialog_by_rounds
    
    def _calculate_interview_stats(self, simulation: InterviewSimulation) -> Dict[str, Any]:
        """Расчет статистики интервью."""
        messages = simulation.dialog_messages
        hr_messages = [msg for msg in messages if msg.speaker == "HR"]
        candidate_messages = [msg for msg in messages if msg.speaker == "Candidate"]
        
        # Средняя длина ответов
        avg_hr_length = sum(len(msg.message) for msg in hr_messages) / len(hr_messages) if hr_messages else 0
        avg_candidate_length = sum(len(msg.message) for msg in candidate_messages) / len(candidate_messages) if candidate_messages else 0
        
        # Количество ключевых моментов
        total_key_points = sum(len(msg.key_points) for msg in messages)
        
        return {
            "total_rounds": simulation.total_rounds_completed,
            "total_messages": len(messages),
            "hr_questions": len(hr_messages),
            "candidate_answers": len(candidate_messages),
            "avg_hr_question_length": int(avg_hr_length),
            "avg_candidate_answer_length": int(avg_candidate_length),
            "total_key_points": total_key_points,
            "question_types_covered": len(simulation.covered_question_types)
        }
    
    def _analyze_question_coverage(self, simulation: InterviewSimulation) -> List[Dict[str, Any]]:
        """Анализ покрытия типов вопросов."""
        covered_types = simulation.covered_question_types
        
        # Все возможные типы вопросов
        all_types = [
            QuestionType.INTRODUCTION,
            QuestionType.TECHNICAL_SKILLS, 
            QuestionType.EXPERIENCE_DEEP_DIVE,
            QuestionType.BEHAVIORAL_STAR,
            QuestionType.PROBLEM_SOLVING,
            QuestionType.MOTIVATION,
            QuestionType.CULTURE_FIT,
            QuestionType.LEADERSHIP,
            QuestionType.FINAL
        ]
        
        coverage = []
        for q_type in all_types:
            is_covered = q_type in covered_types
            coverage.append({
                "type": q_type.value,
                "type_localized": self._localize_question_type(q_type.value),
                "covered": is_covered,
                "css_class": "covered" if is_covered else "not-covered"
            })
        
        return coverage