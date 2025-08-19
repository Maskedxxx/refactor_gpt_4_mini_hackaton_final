# src/llm_interview_simulation/assessment_engine.py
# --- agent_meta ---
# role: interview-simulation-assessment-engine  
# owner: @backend
# contract: Адаптированная система оценки интервью для LLM Features Framework
# last_reviewed: 2025-08-18
# interfaces:
#   - ProfessionalAssessmentEngine (основной класс оценки)
# --- /agent_meta ---

"""
Адаптированная система профессиональной оценки результатов интервью.

Это упрощенная версия оригинального Assessment Engine, адаптированная
для работы с LLM Features Framework и унифицированными моделями данных.

В будущих итерациях здесь будет полная интеграция с LLM для генерации
детальных оценок по каждой компетенции.
"""

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Tuple

from src.utils import get_logger
from src.parsing.llm.client import LLMClient

from .models import (
    DialogMessage, InterviewAssessment, CompetencyScore, CompetencyArea,
    CandidateProfile, CandidateLevel, ITRole, QuestionType
)
from .config import default_settings

logger = get_logger(__name__)


class ProfessionalAssessmentEngine:
    """Система профессиональной оценки результатов интервью.
    
    Анализирует ход интервью и генерирует всестороннюю оценку кандидата
    включая анализ компетенций, выявление сильных/слабых сторон и рекомендации.
    
    Примечание: Это адаптированная версия для первой итерации. 
    В будущем будет добавлена полная LLM интеграция для более детального анализа.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Инициализация системы оценки.
        
        Args:
            llm_client: LLM клиент для генерации оценок (опционально)
        """
        self.llm_client = llm_client
        self.logger = logger.getChild("AssessmentEngine")
        self.settings = default_settings
        
        self.logger.info("Инициализирована система профессиональной оценки")
    
    async def generate_comprehensive_assessment(self,
                                              resume_data: Dict[str, Any],
                                              vacancy_data: Dict[str, Any], 
                                              dialog_messages: List[DialogMessage],
                                              candidate_profile: CandidateProfile) -> InterviewAssessment:
        """Генерирует всестороннюю оценку интервью.
        
        Args:
            resume_data: Данные резюме в формате словаря
            vacancy_data: Данные вакансии в формате словаря
            dialog_messages: История диалога интервью
            candidate_profile: Профиль кандидата
            
        Returns:
            InterviewAssessment: Детальная оценка результатов интервью
        """
        self.logger.info("Начинаем генерацию всесторонней оценки интервью")
        
        if not dialog_messages:
            self.logger.warning("Нет сообщений диалога для оценки")
            return self._create_empty_assessment()
        
        # 1. Оцениваем каждую компетенцию
        competency_scores = await self._assess_competencies(
            dialog_messages, candidate_profile, vacancy_data
        )
        
        # 2. Определяем общую рекомендацию
        overall_recommendation = self._determine_overall_recommendation(competency_scores)
        
        # 3. Анализируем сильные и слабые стороны
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            dialog_messages, candidate_profile
        )
        
        # 4. Выявляем красные флаги
        red_flags = self._detect_red_flags(dialog_messages, candidate_profile)
        
        # 5. Оцениваем культурное соответствие
        cultural_fit_score = self._assess_cultural_fit(dialog_messages, vacancy_data)
        
        assessment = InterviewAssessment(
            overall_recommendation=overall_recommendation,
            competency_scores=competency_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            red_flags=red_flags,
            cultural_fit_score=cultural_fit_score
        )
        
        self.logger.info(f"Оценка создана: {overall_recommendation}, средний балл: {assessment.average_competency_score:.1f}")
        return assessment
    
    async def generate_detailed_feedback(self,
                                        assessment: InterviewAssessment,
                                        candidate_profile: CandidateProfile) -> Dict[str, str]:
        """Генерирует детальную обратную связь для кандидата.
        
        Args:
            assessment: Оценка результатов интервью
            candidate_profile: Профиль кандидата
            
        Returns:
            Dict[str, str]: Словарь с текстовыми рекомендациями
        """
        self.logger.info("Генерируем детальную обратную связь")
        
        try:
            # В будущем здесь будет LLM генерация
            # Пока используем базовый алгоритм
            feedback = self._create_structured_feedback(assessment, candidate_profile)
            
            self.logger.debug("Обратная связь сгенерирована")
            return feedback
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации обратной связи: {e}")
            return self._create_fallback_feedback(assessment, candidate_profile)
    
    async def _assess_competencies(self,
                                 dialog_messages: List[DialogMessage],
                                 candidate_profile: CandidateProfile,
                                 vacancy_data: Dict[str, Any]) -> List[CompetencyScore]:
        """Оценивает каждую компетенцию отдельно.
        
        Args:
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            vacancy_data: Данные вакансии
            
        Returns:
            List[CompetencyScore]: Список оценок по компетенциям
        """
        self.logger.debug("Начинаем оценку компетенций")
        
        # Получаем релевантные компетенции для уровня кандидата
        competencies_to_assess = self._get_relevant_competencies(candidate_profile)
        
        competency_scores = []
        for competency in competencies_to_assess:
            score_data = await self._assess_single_competency(
                competency, dialog_messages, candidate_profile, vacancy_data
            )
            competency_scores.append(score_data)
        
        self.logger.debug(f"Оценено {len(competency_scores)} компетенций")
        return competency_scores
    
    def _get_relevant_competencies(self, candidate_profile: CandidateProfile) -> List[CompetencyArea]:
        """Определяет релевантные компетенции для оценки.
        
        Args:
            candidate_profile: Профиль кандидата
            
        Returns:
            List[CompetencyArea]: Список компетенций для оценки
        """
        # Получаем компетенции для уровня из настроек
        level_competencies = self.settings.level_competencies.get(
            candidate_profile.detected_level,
            self.settings.level_competencies[CandidateLevel.MIDDLE]
        )
        
        competencies = level_competencies.copy()
        
        # Добавляем специфичные компетенции для ролей
        if candidate_profile.detected_role == ITRole.DATA_SCIENTIST:
            if CompetencyArea.LEARNING_ABILITY not in competencies:
                competencies.append(CompetencyArea.LEARNING_ABILITY)
        
        if candidate_profile.management_experience:
            if CompetencyArea.LEADERSHIP not in competencies:
                competencies.append(CompetencyArea.LEADERSHIP)
        
        # Всегда оцениваем культурное соответствие
        if CompetencyArea.CULTURAL_FIT not in competencies:
            competencies.append(CompetencyArea.CULTURAL_FIT)
        
        self.logger.debug(f"Выбрано {len(competencies)} компетенций для оценки")
        return competencies
    
    async def _assess_single_competency(self,
                                      competency: CompetencyArea,
                                      dialog_messages: List[DialogMessage],
                                      candidate_profile: CandidateProfile,
                                      vacancy_data: Dict[str, Any]) -> CompetencyScore:
        """Оценивает одну конкретную компетенцию.
        
        Args:
            competency: Компетенция для оценки
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            vacancy_data: Данные вакансии
            
        Returns:
            CompetencyScore: Оценка компетенции
        """
        self.logger.debug(f"Оцениваем компетенцию: {competency.value}")
        
        # Получаем релевантные ответы для компетенции
        relevant_answers = self._extract_relevant_answers(dialog_messages, competency)
        
        if not relevant_answers:
            # Если нет релевантных ответов, даем базовую оценку
            return self._create_default_competency_score(competency)
        
        # Вычисляем оценку на основе качества ответов
        scores = [msg.response_quality or 3 for msg in relevant_answers]
        avg_score = sum(scores) / len(scores)
        
        # Корректируем оценку в зависимости от компетенции и контекста
        adjusted_score = self._adjust_competency_score(
            competency, avg_score, relevant_answers, candidate_profile
        )
        
        # Извлекаем доказательства из ответов
        evidence = self._extract_evidence(relevant_answers, competency)
        
        # Генерируем рекомендации по улучшению
        improvement_notes = self._generate_improvement_notes(competency, adjusted_score, candidate_profile)
        
        return CompetencyScore(
            area=competency,
            score=max(1, min(5, round(adjusted_score))),
            evidence=evidence,
            improvement_notes=improvement_notes
        )
    
    def _extract_relevant_answers(self,
                                dialog_messages: List[DialogMessage],
                                competency: CompetencyArea) -> List[DialogMessage]:
        """Извлекает ответы, релевантные для конкретной компетенции.
        
        Args:
            dialog_messages: История диалога
            competency: Компетенция для анализа
            
        Returns:
            List[DialogMessage]: Релевантные ответы кандидата
        """
        # Карта типов вопросов к компетенциям
        question_competency_map = {
            CompetencyArea.TECHNICAL_EXPERTISE: [
                QuestionType.TECHNICAL_SKILLS, 
                QuestionType.EXPERIENCE_DEEP_DIVE
            ],
            CompetencyArea.COMMUNICATION: [
                QuestionType.INTRODUCTION, 
                QuestionType.FINAL
            ],
            CompetencyArea.PROBLEM_SOLVING: [
                QuestionType.PROBLEM_SOLVING, 
                QuestionType.BEHAVIORAL_STAR
            ],
            CompetencyArea.TEAMWORK: [
                QuestionType.BEHAVIORAL_STAR
            ],
            CompetencyArea.LEADERSHIP: [
                QuestionType.LEADERSHIP, 
                QuestionType.BEHAVIORAL_STAR
            ],
            CompetencyArea.ADAPTABILITY: [
                QuestionType.BEHAVIORAL_STAR, 
                QuestionType.PROBLEM_SOLVING
            ],
            CompetencyArea.LEARNING_ABILITY: [
                QuestionType.TECHNICAL_SKILLS, 
                QuestionType.MOTIVATION
            ],
            CompetencyArea.MOTIVATION: [
                QuestionType.MOTIVATION, 
                QuestionType.INTRODUCTION
            ],
            CompetencyArea.CULTURAL_FIT: [
                QuestionType.CULTURE_FIT, 
                QuestionType.MOTIVATION
            ]
        }
        
        relevant_question_types = question_competency_map.get(competency, [])
        
        relevant_answers = []
        for i, msg in enumerate(dialog_messages):
            if msg.speaker == "Candidate":
                # Находим соответствующий вопрос HR
                hr_question = None
                if i > 0 and dialog_messages[i-1].speaker == "HR":
                    hr_question = dialog_messages[i-1]
                
                # Проверяем релевантность
                if (hr_question and 
                    hr_question.question_type in relevant_question_types):
                    relevant_answers.append(msg)
                elif not relevant_question_types:  # Если нет специфичных типов
                    relevant_answers.append(msg)
        
        self.logger.debug(f"Найдено {len(relevant_answers)} релевантных ответов для {competency.value}")
        return relevant_answers
    
    def _adjust_competency_score(self,
                                competency: CompetencyArea,
                                base_score: float,
                                relevant_answers: List[DialogMessage],
                                candidate_profile: CandidateProfile) -> float:
        """Корректирует оценку компетенции на основе контекста.
        
        Args:
            competency: Компетенция
            base_score: Базовая оценка
            relevant_answers: Релевантные ответы
            candidate_profile: Профиль кандидата
            
        Returns:
            float: Скорректированная оценка
        """
        adjusted_score = base_score
        
        # Корректировка по уровню кандидата
        if candidate_profile.detected_level == CandidateLevel.JUNIOR:
            adjusted_score += 0.3  # Более мягкая оценка для junior
        elif candidate_profile.detected_level == CandidateLevel.LEAD:
            adjusted_score -= 0.2  # Более строгая оценка для lead
        
        # Специфичные корректировки по компетенциям
        if competency == CompetencyArea.TECHNICAL_EXPERTISE:
            # Бонус за упоминание технологий
            tech_mentions = sum(
                1 for answer in relevant_answers
                for tech in candidate_profile.key_technologies
                if tech.lower() in answer.message.lower()
            )
            if tech_mentions > 0:
                adjusted_score += min(0.5, tech_mentions * 0.1)
        
        elif competency == CompetencyArea.LEADERSHIP:
            # Только для кандидатов с управленческим опытом
            if not candidate_profile.management_experience:
                adjusted_score -= 0.5
        
        elif competency == CompetencyArea.COMMUNICATION:
            # Бонус за структурированные ответы
            avg_length = sum(len(msg.message) for msg in relevant_answers) / len(relevant_answers)
            if avg_length > 150:  # Детальные ответы
                adjusted_score += 0.3
            elif avg_length < 50:  # Слишком краткие
                adjusted_score -= 0.3
        
        return max(1.0, min(5.0, adjusted_score))
    
    def _extract_evidence(self,
                         relevant_answers: List[DialogMessage],
                         competency: CompetencyArea) -> List[str]:
        """Извлекает доказательства из ответов кандидата.
        
        Args:
            relevant_answers: Релевантные ответы
            competency: Компетенция
            
        Returns:
            List[str]: Список доказательств
        """
        evidence = []
        
        for answer in relevant_answers[:3]:  # Берем первые 3 ответа
            # Извлекаем ключевые фразы из ответа
            message = answer.message
            
            # Ищем конкретные примеры
            examples = re.findall(r'например[^.]*\.', message, re.IGNORECASE)
            evidence.extend(examples[:2])  # Максимум 2 примера с одного ответа
            
            # Если нет примеров, берем первые 100 символов
            if not examples and len(message) > 50:
                evidence.append(f"Раунд {answer.round_number}: {message[:100]}...")
        
        # Если нет конкретных доказательств, добавляем общую информацию
        if not evidence:
            evidence.append(f"Анализ {len(relevant_answers)} ответов кандидата")
        
        return evidence[:3]  # Максимум 3 доказательства
    
    def _generate_improvement_notes(self,
                                   competency: CompetencyArea,
                                   score: float,
                                   candidate_profile: CandidateProfile) -> str:
        """Генерирует рекомендации по улучшению компетенции.
        
        Args:
            competency: Компетенция
            score: Оценка компетенции
            candidate_profile: Профиль кандидата
            
        Returns:
            str: Рекомендации по улучшению
        """
        # Базовые рекомендации по компетенциям
        base_recommendations = {
            CompetencyArea.TECHNICAL_EXPERTISE: "Углубите знания в ключевых технологиях, изучайте best practices",
            CompetencyArea.COMMUNICATION: "Практикуйте структурированное изложение мыслей, приводите конкретные примеры",
            CompetencyArea.PROBLEM_SOLVING: "Развивайте аналитическое мышление, изучайте различные подходы к решению задач",
            CompetencyArea.TEAMWORK: "Участвуйте в командных проектах, развивайте навыки сотрудничества",
            CompetencyArea.LEADERSHIP: "Изучайте принципы управления, практикуйте менторство коллег",
            CompetencyArea.ADAPTABILITY: "Будьте открыты к изменениям, изучайте новые технологии и подходы",
            CompetencyArea.LEARNING_ABILITY: "Непрерывно обучайтесь, следите за трендами в индустрии",
            CompetencyArea.MOTIVATION: "Четко формулируйте карьерные цели, изучайте компанию перед интервью",
            CompetencyArea.CULTURAL_FIT: "Изучайте корпоративную культуру, адаптируйте стиль коммуникации"
        }
        
        base_note = base_recommendations.get(
            competency, 
            f"Продолжайте развивать навыки в области {competency.value}"
        )
        
        # Корректировка по оценке
        if score >= 4.5:
            return f"Отлично! {base_note.replace('Развивайте', 'Поддерживайте высокий уровень')}"
        elif score >= 3.5:
            return f"Хорошо. {base_note}"
        elif score >= 2.5:
            return f"Требует внимания. {base_note}"
        else:
            return f"Критично важно улучшить. {base_note}"
    
    def _create_default_competency_score(self, competency: CompetencyArea) -> CompetencyScore:
        """Создает дефолтную оценку компетенции.
        
        Args:
            competency: Компетенция
            
        Returns:
            CompetencyScore: Дефолтная оценка
        """
        return CompetencyScore(
            area=competency,
            score=3,
            evidence=["Недостаточно данных для детальной оценки"],
            improvement_notes=f"Требуется дополнительная оценка компетенции {competency.value}"
        )
    
    def _determine_overall_recommendation(self, competency_scores: List[CompetencyScore]) -> str:
        """Определяет общую рекомендацию на основе оценок компетенций.
        
        Args:
            competency_scores: Оценки по компетенциям
            
        Returns:
            str: Общая рекомендация (hire/conditional_hire/reject)
        """
        if not competency_scores:
            return "conditional_hire"
        
        # Вычисляем средний балл
        avg_score = sum(cs.score for cs in competency_scores) / len(competency_scores)
        
        # Проверяем критичные компетенции
        technical_scores = [
            cs.score for cs in competency_scores 
            if cs.area == CompetencyArea.TECHNICAL_EXPERTISE
        ]
        communication_scores = [
            cs.score for cs in competency_scores 
            if cs.area == CompetencyArea.COMMUNICATION
        ]
        
        technical_score = technical_scores[0] if technical_scores else avg_score
        communication_score = communication_scores[0] if communication_scores else avg_score
        
        # Логика принятия решения из настроек
        hire_threshold = self.settings.assessment_settings["hire_threshold"]
        conditional_threshold = self.settings.assessment_settings["conditional_hire_threshold"]
        
        if (avg_score >= hire_threshold and 
            technical_score >= 4 and 
            communication_score >= 3):
            return "hire"
        elif (avg_score >= conditional_threshold and 
              technical_score >= 3 and 
              communication_score >= 3):
            return "conditional_hire"
        else:
            return "reject"
    
    def _analyze_strengths_weaknesses(self,
                                    dialog_messages: List[DialogMessage],
                                    candidate_profile: CandidateProfile) -> Tuple[List[str], List[str]]:
        """Анализирует сильные и слабые стороны кандидата.
        
        Args:
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            
        Returns:
            Tuple[List[str], List[str]]: Сильные и слабые стороны
        """
        candidate_responses = [msg for msg in dialog_messages if msg.speaker == "Candidate"]
        
        if not candidate_responses:
            return ["Готовность к диалогу"], ["Недостаточно данных для анализа"]
        
        avg_quality = sum(msg.response_quality or 3 for msg in candidate_responses) / len(candidate_responses)
        
        strengths = []
        weaknesses = []
        
        # Анализ качества ответов
        if avg_quality >= 4.0:
            strengths.extend(["Детальные и продуманные ответы", "Высокое качество коммуникации"])
        elif avg_quality >= 3.0:
            strengths.append("Адекватное качество ответов")
        else:
            weaknesses.append("Поверхностные ответы")
        
        # Анализ длины ответов
        avg_length = sum(len(msg.message) for msg in candidate_responses) / len(candidate_responses)
        if avg_length > 200:
            strengths.append("Способность давать развернутые ответы")
        elif avg_length < 80:
            weaknesses.append("Склонность к слишком кратким ответам")
        
        # Анализ опыта
        if candidate_profile.years_of_experience:
            if candidate_profile.years_of_experience >= 5:
                strengths.append("Богатый профессиональный опыт")
            elif candidate_profile.years_of_experience >= 2:
                strengths.append("Достаточный профессиональный опыт")
            else:
                weaknesses.append("Ограниченный профессиональный опыт")
        
        # Анализ технологий
        if len(candidate_profile.key_technologies) >= 5:
            strengths.append("Широкий технологический стек")
        elif len(candidate_profile.key_technologies) < 3:
            weaknesses.append("Ограниченный набор технологий")
        
        # Управленческий опыт
        if candidate_profile.management_experience:
            strengths.append("Опыт управления и лидерства")
        
        # Проверяем что есть хотя бы одна сильная и слабая сторона
        if not strengths:
            strengths.append("Готовность к профессиональному развитию")
        
        if not weaknesses:
            weaknesses.append("Возможности для дальнейшего роста")
        
        return strengths[:4], weaknesses[:3]  # Ограничиваем количество
    
    def _detect_red_flags(self,
                         dialog_messages: List[DialogMessage],
                         candidate_profile: CandidateProfile) -> List[str]:
        """Выявляет красные флаги в ответах кандидата.
        
        Args:
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            
        Returns:
            List[str]: Список красных флагов
        """
        red_flags = []
        candidate_responses = [msg for msg in dialog_messages if msg.speaker == "Candidate"]
        
        if not candidate_responses:
            return red_flags
        
        # Проверяем слишком короткие ответы
        short_responses = [msg for msg in candidate_responses if len(msg.message) < 50]
        if len(short_responses) >= len(candidate_responses) * 0.6:
            red_flags.append("Большинство ответов слишком краткие")
        
        # Проверяем низкое качество ответов
        low_quality_responses = [
            msg for msg in candidate_responses 
            if (msg.response_quality or 3) <= 2
        ]
        if len(low_quality_responses) >= len(candidate_responses) * 0.4:
            red_flags.append("Низкое качество большинства ответов")
        
        # Проверяем отсутствие конкретики
        responses_text = " ".join(msg.message.lower() for msg in candidate_responses)
        concrete_keywords = ['например', 'проект', 'задача', 'результат', 'опыт']
        concrete_mentions = sum(1 for kw in concrete_keywords if kw in responses_text)
        
        if concrete_mentions < len(candidate_responses) * 0.3:
            red_flags.append("Недостаток конкретных примеров в ответах")
        
        # Проверяем паттерны проблемного поведения
        problem_patterns = {
            "Негатив о предыдущих работодателях": [
                r"ужасн\w+", r"кошмар\w+", r"плох\w+\s+(начальник|команда|компания)"
            ],
            "Неопределенность в ответах": [
                r"не\s+знаю", r"может\s+быть", r"что-то\s+такое", r"как-то\s+так"
            ]
        }
        
        for flag_type, patterns in problem_patterns.items():
            for pattern in patterns:
                if re.search(pattern, responses_text):
                    red_flags.append(flag_type)
                    break  # Один флаг этого типа достаточно
        
        return red_flags
    
    def _assess_cultural_fit(self,
                           dialog_messages: List[DialogMessage],
                           vacancy_data: Dict[str, Any]) -> int:
        """Оценивает культурное соответствие кандидата.
        
        Args:
            dialog_messages: История диалога
            vacancy_data: Данные вакансии
            
        Returns:
            int: Оценка культурного соответствия (1-5)
        """
        # Ищем ответы на вопросы о мотивации и культуре
        relevant_messages = []
        for i, msg in enumerate(dialog_messages):
            if (msg.speaker == "Candidate" and i > 0 and 
                dialog_messages[i-1].speaker == "HR"):
                hr_question = dialog_messages[i-1]
                if hr_question.question_type in [QuestionType.MOTIVATION, QuestionType.CULTURE_FIT]:
                    relevant_messages.append(msg)
        
        if not relevant_messages:
            return 3  # Нейтральная оценка
        
        # Базовая оценка на основе качества ответов
        scores = [msg.response_quality or 3 for msg in relevant_messages]
        avg_score = sum(scores) / len(scores)
        
        # Корректировки на основе содержания
        responses_text = " ".join(msg.message.lower() for msg in relevant_messages)
        
        # Позитивные индикаторы
        positive_keywords = [
            'интересно', 'развитие', 'команда', 'цель', 'мотивация', 
            'обучение', 'рост', 'достижение', 'результат'
        ]
        positive_score = sum(1 for kw in positive_keywords if kw in responses_text)
        
        # Негативные индикаторы
        negative_keywords = [
            'только деньги', 'все равно', 'не важно', 'любая работа'
        ]
        negative_score = sum(1 for kw in negative_keywords if kw in responses_text)
        
        # Корректируем оценку
        final_score = avg_score + (positive_score * 0.2) - (negative_score * 0.5)
        
        return max(1, min(5, round(final_score)))
    
    def _create_structured_feedback(self,
                                   assessment: InterviewAssessment,
                                   candidate_profile: CandidateProfile) -> Dict[str, str]:
        """Создает структурированную обратную связь.
        
        Args:
            assessment: Оценка интервью
            candidate_profile: Профиль кандидата
            
        Returns:
            Dict[str, str]: Структурированная обратная связь
        """
        avg_score = assessment.average_competency_score
        
        # HR Assessment
        hr_assessment = self._create_hr_assessment(assessment, candidate_profile, avg_score)
        
        # Performance Analysis  
        performance_analysis = self._create_performance_analysis(assessment, avg_score)
        
        # Improvement Recommendations
        improvement_recommendations = self._create_improvement_recommendations(assessment)
        
        return {
            'hr_assessment': hr_assessment,
            'performance_analysis': performance_analysis,
            'improvement_recommendations': improvement_recommendations
        }
    
    def _create_hr_assessment(self,
                             assessment: InterviewAssessment,
                             candidate_profile: CandidateProfile,
                             avg_score: float) -> str:
        """Создает HR оценку."""
        
        level_text = candidate_profile.detected_level.value
        role_text = candidate_profile.detected_role.value.replace('_', ' ')
        
        performance_text = self._score_to_text(avg_score)
        recommendation_text = {
            "hire": "рекомендуется к найму",
            "conditional_hire": "рекомендуется к найму с условиями", 
            "reject": "не рекомендуется к найму"
        }[assessment.overall_recommendation]
        
        hr_assessment = f"Кандидат уровня {level_text} на позицию {role_text} "
        hr_assessment += f"продемонстрировал {performance_text} результат (средняя оценка {avg_score:.1f}/5). "
        hr_assessment += f"На основе анализа интервью кандидат {recommendation_text}."
        
        if assessment.red_flags:
            hr_assessment += f" Выявлено {len(assessment.red_flags)} критических замечаний."
        
        return hr_assessment
    
    def _create_performance_analysis(self,
                                    assessment: InterviewAssessment,
                                    avg_score: float) -> str:
        """Создает анализ выступления."""
        
        analysis = "Детальный анализ выступления кандидата: "
        
        # Сильные стороны
        if assessment.strengths:
            analysis += f"сильные стороны включают {', '.join(assessment.strengths[:3])}. "
        
        # Слабые стороны
        if assessment.weaknesses:
            analysis += f"Области для развития: {', '.join(assessment.weaknesses[:2])}. "
        
        # Анализ компетенций
        top_competencies = sorted(assessment.competency_scores, key=lambda x: x.score, reverse=True)
        if top_competencies:
            best_comp = top_competencies[0]
            analysis += f"Наиболее сильная компетенция: {best_comp.area.value} ({best_comp.score}/5). "
        
        if len(top_competencies) > 1:
            worst_comp = top_competencies[-1]
            if worst_comp.score < 4:
                analysis += f"Требует развития: {worst_comp.area.value} ({worst_comp.score}/5). "
        
        # Культурное соответствие
        analysis += f"Культурное соответствие оценено в {assessment.cultural_fit_score}/5 баллов."
        
        return analysis
    
    def _create_improvement_recommendations(self, assessment: InterviewAssessment) -> str:
        """Создает рекомендации по улучшению."""
        
        recommendations = []
        
        # Рекомендации на основе слабых компетенций
        weak_competencies = [cs for cs in assessment.competency_scores if cs.score < 4]
        for comp in weak_competencies[:3]:  # Максимум 3 рекомендации
            if comp.improvement_notes:
                recommendations.append(comp.improvement_notes)
        
        # Общие рекомендации на основе красных флагов
        if assessment.red_flags:
            if "краткие ответы" in str(assessment.red_flags).lower():
                recommendations.append("Практикуйте развернутые ответы с конкретными примерами")
            if "качество" in str(assessment.red_flags).lower():
                recommendations.append("Улучшите структуру ответов, используйте методику STAR")
        
        # Рекомендации по культурному соответствию
        if assessment.cultural_fit_score < 4:
            recommendations.append("Изучите корпоративную культуру компаний перед интервью")
        
        # Если нет специфичных рекомендаций
        if not recommendations:
            recommendations.append("Продолжайте развивать профессиональные навыки и готовиться к интервью")
        
        return ". ".join(recommendations[:4]) + "."  # Максимум 4 рекомендации
    
    def _score_to_text(self, score: float) -> str:
        """Конвертирует численную оценку в текстовое описание."""
        
        if score >= 4.5:
            return "превосходный"
        elif score >= 4.0:
            return "отличный"
        elif score >= 3.5:
            return "хороший"
        elif score >= 3.0:
            return "удовлетворительный"
        elif score >= 2.5:
            return "ниже среднего"
        else:
            return "неудовлетворительный"
    
    def _create_fallback_feedback(self,
                                 assessment: InterviewAssessment,
                                 candidate_profile: CandidateProfile) -> Dict[str, str]:
        """Создает базовую обратную связь в случае ошибки."""
        
        avg_score = assessment.average_competency_score
        
        return {
            'hr_assessment': f"Кандидат показал результат {avg_score:.1f}/5. Рекомендация: {assessment.overall_recommendation}.",
            'performance_analysis': f"Проанализированы компетенции кандидата. Культурное соответствие: {assessment.cultural_fit_score}/5.",
            'improvement_recommendations': "Продолжайте развивать профессиональные навыки. Готовьтесь к интервью более детально."
        }
    
    def _create_empty_assessment(self) -> InterviewAssessment:
        """Создает пустую оценку для случаев без диалога."""
        
        return InterviewAssessment(
            overall_recommendation="conditional_hire",
            competency_scores=[
                CompetencyScore(
                    area=CompetencyArea.COMMUNICATION,
                    score=3,
                    evidence=["Нет данных для анализа"],
                    improvement_notes="Требуется проведение интервью"
                )
            ],
            strengths=["Готовность к интервью"],
            weaknesses=["Нет данных для полной оценки"],
            red_flags=[],
            cultural_fit_score=3
        )