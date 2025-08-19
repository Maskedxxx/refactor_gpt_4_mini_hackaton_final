# src/llm_interview_simulation/service.py
# --- agent_meta ---
# role: interview-simulation-service
# owner: @backend
# contract: Главный генератор симуляции интервью, интегрированный с LLM Features Framework
# last_reviewed: 2025-08-18
# interfaces:
#   - LLMInterviewSimulationGenerator (implements AbstractLLMGenerator[InterviewSimulation])
# --- /agent_meta ---

from __future__ import annotations

import asyncio
from typing import Optional, List, Tuple, Dict, Any

from src.utils import get_logger
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.parsing.llm.client import LLMClient
from src.parsing.llm.prompt import Prompt
from pydantic import BaseModel
from src.llm_features.base.generator import AbstractLLMGenerator
from src.llm_features.base.interfaces import IFeatureValidator, IFeatureFormatter
from src.llm_features.base.options import BaseLLMOptions
from src.llm_features.base.errors import BaseLLMError

from .models import (
    InterviewSimulation, DialogMessage, CandidateProfile, InterviewConfiguration,
    QuestionType, InterviewAssessment, CompetencyScore, CompetencyArea, CandidateLevel
)
from .options import InterviewSimulationOptions, ProgressCallbackType
from .config import default_settings, get_question_types_for_round
from .formatter import (
    format_resume_for_interview_simulation,
    format_vacancy_for_interview_simulation, 
    format_dialog_history,
    create_candidate_profile_and_config
)
from .prompts import InterviewPromptBuilder
from .assessment_engine import ProfessionalAssessmentEngine

logger = get_logger(__name__)


class LLMInterviewSimulationGenerator(AbstractLLMGenerator[InterviewSimulation]):
    """Генератор симуляции интервью, интегрированный с LLM Features Framework.
    
    Реализует полный цикл проведения симулированного интервью между AI HR-менеджером
    и AI кандидатом на основе реального резюме и вакансии.
    
    Ключевые возможности:
    - Адаптивные вопросы в зависимости от уровня кандидата
    - Структурированная оценка по компетенциям
    - Интеграция с существующей архитектурой LLM Features
    - Поддержка различных типов интервью (technical, behavioral, etc.)
    """
    
    def __init__(self, 
                 *,
                 llm: Optional[LLMClient] = None,
                 validator: Optional[IFeatureValidator] = None,
                 formatter: Optional[IFeatureFormatter] = None,
                 openai_api_key: Optional[str] = None,
                 openai_model_name: Optional[str] = None):
        """Инициализация генератора симуляции интервью.
        
        Args:
            llm: LLM клиент для взаимодействия с языковой моделью
            validator: Валидатор для проверки качества результатов
            formatter: Форматтер для вывода результатов
            openai_api_key: API ключ OpenAI (если не задан llm)
            openai_model_name: Название модели OpenAI (если не задан llm)
        """
        super().__init__(
            llm=llm,
            validator=validator,
            formatter=formatter,
            openai_api_key=openai_api_key or default_settings.openai_api_key,
            openai_model_name=openai_model_name or default_settings.openai_model_name
        )
        
        # Инициализируем компоненты для симуляции интервью
        self.prompt_builder = InterviewPromptBuilder()
        self.assessment_engine = ProfessionalAssessmentEngine()
        
        # Настройки по умолчанию
        self.settings = default_settings
        
        self._log.info("Инициализирован генератор симуляции интервью")
    
    async def generate(
        self, 
        resume: ResumeInfo, 
        vacancy: VacancyInfo, 
        options: BaseLLMOptions
    ) -> InterviewSimulation:
        """Переопределенный workflow генерации для симуляции интервью.
        
        Отличается от базового тем, что передает контекст резюме и вакансии
        в _call_llm метод через специальные атрибуты в опциях.
        """
        try:
            self._log.info(
                "Запуск генерации фичи %s, версия=%s", 
                self.get_feature_name(), 
                options.prompt_version
            )
            
            # 1. Подготовка опций с дефолтами
            merged_options = self._merge_with_defaults(options)
            
            # 2. Добавляем контекст резюме и вакансии в опции для передачи в _call_llm
            # Это нужно потому что AbstractLLMGenerator не предусматривает передачу
            # дополнительных параметров в _call_llm кроме prompt и options
            merged_options._resume_context = resume
            merged_options._vacancy_context = vacancy
            
            # 3. Сборка промпта (для симуляции это только первый промпт)
            prompt = await self._build_prompt(resume, vacancy, merged_options)
            
            # 4. Вызов LLM (здесь происходит вся логика симуляции)
            result = await self._call_llm(prompt, merged_options)
            
            # 5. Валидация
            if merged_options.quality_checks and self._validator:
                # Для симуляции интервью валидация пока не реализована
                self._log.debug("Валидация результатов симуляции интервью пропущена")
            
            self._log.info("Генерация фичи %s завершена успешно", self.get_feature_name())
            return result
            
        except Exception as e:
            self._log.error("Ошибка генерации фичи %s: %s", self.get_feature_name(), str(e))
            raise BaseLLMError(f"Generation failed for {self.get_feature_name()}: {str(e)}") from e
    
    async def _build_prompt(self, 
                           resume: ResumeInfo, 
                           vacancy: VacancyInfo, 
                           options: InterviewSimulationOptions) -> Prompt:
        """Строит промпт для симуляции интервью.
        
        Примечание: Это метод из AbstractLLMGenerator, но для симуляции интервью
        мы используем более сложную логику с множественными промптами.
        Здесь мы возвращаем промпт для первого вопроса HR.
        
        Args:
            resume: Информация о резюме
            vacancy: Информация о вакансии  
            options: Опции симуляции
            
        Returns:
            Prompt: Промпт для первого вопроса HR
        """
        self._log.debug("Строим начальный промпт для симуляции интервью")
        
        # Создаем профиль кандидата и конфигурацию
        candidate_profile, interview_config = create_candidate_profile_and_config(resume, vacancy)
        
        # Форматируем данные
        formatted_resume = format_resume_for_interview_simulation(resume)
        formatted_vacancy = format_vacancy_for_interview_simulation(vacancy)
        formatted_history = format_dialog_history([])  # Пустая история для первого вопроса
        
        # Определяем тип первого вопроса
        first_question_types = get_question_types_for_round(1)
        first_question_type = first_question_types[0] if first_question_types else QuestionType.INTRODUCTION
        
        # Строим промпт для первого вопроса HR
        prompt = self.prompt_builder.build_hr_prompt(
            formatted_resume=formatted_resume,
            formatted_vacancy=formatted_vacancy,
            formatted_history=formatted_history,
            round_number=1,
            question_type=first_question_type,
            candidate_profile=candidate_profile,
            interview_config=interview_config,
            options=options
        )
        
        return prompt
    
    async def _call_llm(self, prompt: Prompt, options: InterviewSimulationOptions) -> InterviewSimulation:
        """Выполняет полную симуляцию интервью с использованием LLM.
        
        Это основной метод, который координирует весь процесс:
        1. Анализ профиля кандидата
        2. Проведение многораундового диалога
        3. Оценка результатов
        4. Формирование итогового отчета
        
        Args:
            prompt: Начальный промпт (используется для извлечения контекста)
            options: Опции симуляции интервью
            
        Returns:
            InterviewSimulation: Результат полной симуляции интервью
        """
        self._log.info("Начинаем полную симуляцию интервью")
        
        # Примечание: prompt здесь содержит контекст, но мы будем использовать
        # более сложную логику симуляции с несколькими вызовами LLM
        
        # Для начала нам нужны resume и vacancy, но AbstractLLMGenerator их не передает
        # Поэтому мы сохраним их в контексте через опции
        if not hasattr(options, '_resume_context') or not hasattr(options, '_vacancy_context'):
            raise ValueError("Resume и Vacancy контекст должны быть переданы через опции")
        
        resume = options._resume_context
        vacancy = options._vacancy_context
        
        # 1. Создаем профиль кандидата и конфигурацию интервью
        candidate_profile, interview_config = create_candidate_profile_and_config(resume, vacancy)
        
        # Применяем настройки из опций
        interview_config = self._apply_options_to_config(interview_config, options)
        
        self._log.info(f"Профиль: {candidate_profile.detected_level.value} {candidate_profile.detected_role.value}")
        self._log.info(f"Конфигурация: {interview_config.target_rounds} раундов")
        
        # 2. Подготавливаем форматированные данные
        formatted_resume = format_resume_for_interview_simulation(resume)
        formatted_vacancy = format_vacancy_for_interview_simulation(vacancy)
        
        # 3. Проводим многораундовый диалог
        dialog_messages = await self._conduct_interview_dialog(
            formatted_resume=formatted_resume,
            formatted_vacancy=formatted_vacancy,
            candidate_profile=candidate_profile,
            interview_config=interview_config,
            options=options
        )
        
        # 4. Генерируем профессиональную оценку
        assessment = await self._generate_assessment(
            resume=resume,
            vacancy=vacancy,
            dialog_messages=dialog_messages,
            candidate_profile=candidate_profile,
            options=options
        )
        
        # 5. Генерируем текстовые рекомендации
        feedback = await self._generate_feedback(assessment, candidate_profile)
        
        # 6. Собираем метаданные
        simulation_metadata = self._create_simulation_metadata(
            dialog_messages, candidate_profile, interview_config, options
        )
        
        # 7. Создаем итоговый объект симуляции
        simulation = InterviewSimulation(
            position_title=getattr(vacancy, 'name', 'IT позиция'),
            candidate_name=self._extract_candidate_name(resume),
            company_context=self._create_company_context(vacancy),
            candidate_profile=candidate_profile,
            interview_config=interview_config,
            dialog_messages=dialog_messages,
            assessment=assessment,
            hr_assessment=feedback['hr_assessment'],
            candidate_performance_analysis=feedback['performance_analysis'],
            improvement_recommendations=feedback['improvement_recommendations'],
            simulation_metadata=simulation_metadata
        )
        
        self._log.info(f"Симуляция интервью завершена: {len(dialog_messages)} сообщений, рекомендация: {assessment.overall_recommendation}")
        return simulation
    
    async def _conduct_interview_dialog(self,
                                       formatted_resume: str,
                                       formatted_vacancy: str,
                                       candidate_profile: CandidateProfile,
                                       interview_config: InterviewConfiguration,
                                       options: InterviewSimulationOptions) -> List[DialogMessage]:
        """Проводит полный диалог интервью между HR и кандидатом.
        
        Args:
            formatted_resume: Отформатированное резюме
            formatted_vacancy: Отформатированная вакансия
            candidate_profile: Профиль кандидата
            interview_config: Конфигурация интервью
            options: Опции симуляции
            
        Returns:
            List[DialogMessage]: Список всех сообщений диалога
        """
        self._log.info(f"Начинаем диалог интервью на {interview_config.target_rounds} раундов")
        
        dialog_messages = []
        
        # Проводим раунды диалога
        for round_num in range(1, interview_config.target_rounds + 1):
            self._log.debug(f"Начинаем раунд {round_num}/{interview_config.target_rounds}")
            
            # Определяем тип вопроса для текущего раунда
            question_type = self._select_question_type_for_round(
                round_num, candidate_profile, dialog_messages
            )
            
            # HR задает вопрос
            hr_question = await self._generate_hr_question(
                formatted_resume=formatted_resume,
                formatted_vacancy=formatted_vacancy,
                dialog_messages=dialog_messages,
                round_number=round_num,
                question_type=question_type,
                candidate_profile=candidate_profile,
                interview_config=interview_config,
                options=options
            )
            
            if not hr_question:
                self._log.warning(f"Не удалось сгенерировать вопрос HR в раунде {round_num}")
                break
            
            # Добавляем вопрос HR в диалог
            hr_message = DialogMessage(
                speaker="HR",
                message=hr_question,
                round_number=round_num,
                question_type=question_type
            )
            dialog_messages.append(hr_message)
            self._log.debug(f"HR задал вопрос типа {question_type.value}")
            
            # Кандидат отвечает
            candidate_answer = await self._generate_candidate_answer(
                formatted_resume=formatted_resume,
                formatted_vacancy=formatted_vacancy,
                dialog_messages=dialog_messages,
                hr_question=hr_question,
                candidate_profile=candidate_profile,
                options=options
            )
            
            if not candidate_answer:
                self._log.warning(f"Не удалось сгенерировать ответ кандидата в раунде {round_num}")
                break
            
            # Оцениваем качество ответа
            response_quality = self._evaluate_response_quality(
                candidate_answer, question_type, candidate_profile
            )
            
            # Добавляем ответ кандидата в диалог
            candidate_message = DialogMessage(
                speaker="Candidate",
                message=candidate_answer,
                round_number=round_num,
                response_quality=response_quality
            )
            dialog_messages.append(candidate_message)
            self._log.debug(f"Кандидат ответил (качество: {response_quality}/5)")
            
            # Небольшая пауза между раундами для более реалистичной симуляции
            if options.enable_progress_callbacks:
                await asyncio.sleep(0.1)
        
        self._log.info(f"Диалог завершен: {len(dialog_messages)} сообщений в {len(dialog_messages)//2} раундах")
        return dialog_messages
    
    async def _generate_hr_question(self,
                                   formatted_resume: str,
                                   formatted_vacancy: str,
                                   dialog_messages: List[DialogMessage],
                                   round_number: int,
                                   question_type: QuestionType,
                                   candidate_profile: CandidateProfile,
                                   interview_config: InterviewConfiguration,
                                   options: InterviewSimulationOptions) -> Optional[str]:
        """Генерирует вопрос HR-менеджера для текущего раунда.
        
        Args:
            formatted_resume: Отформатированное резюме
            formatted_vacancy: Отформатированная вакансия
            dialog_messages: История диалога
            round_number: Номер раунда
            question_type: Тип вопроса
            candidate_profile: Профиль кандидата
            interview_config: Конфигурация интервью
            options: Опции симуляции
            
        Returns:
            Optional[str]: Сгенерированный вопрос или None в случае ошибки
        """
        try:
            # Форматируем историю диалога
            formatted_history = format_dialog_history(dialog_messages)
            
            # Строим промпт для HR
            prompt = self.prompt_builder.build_hr_prompt(
                formatted_resume=formatted_resume,
                formatted_vacancy=formatted_vacancy,
                formatted_history=formatted_history,
                round_number=round_number,
                question_type=question_type,
                candidate_profile=candidate_profile,
                interview_config=interview_config,
                options=options
            )
            
            if options.log_detailed_prompts:
                self._log.debug(f"HR промпт (раунд {round_number}):\n{prompt.system[:200]}...")
            
            # Простая схема для текстового ответа через parse API
            class _TextOnly(BaseModel):
                text: str

            # Генерируем вопрос с настройками для HR
            result = await self._llm.generate_structured(
                prompt=prompt,
                schema=_TextOnly,
                temperature=getattr(options, 'temperature_hr', 0.7),
                max_tokens=getattr(options, 'max_tokens_per_message', 2500)
            )
            
            question = (result.text or "").strip() if result else None
            self._log.debug(f"Сгенерирован вопрос HR длиной {len(question) if question else 0} символов")
            return question
            
        except Exception as e:
            self._log.error(f"Ошибка генерации вопроса HR в раунде {round_number}: {e}")
            return None
    
    async def _generate_candidate_answer(self,
                                        formatted_resume: str,
                                        formatted_vacancy: str,
                                        dialog_messages: List[DialogMessage],
                                        hr_question: str,
                                        candidate_profile: CandidateProfile,
                                        options: InterviewSimulationOptions) -> Optional[str]:
        """Генерирует ответ кандидата на вопрос HR.
        
        Args:
            formatted_resume: Отформатированное резюме
            formatted_vacancy: Отформатированная вакансия
            dialog_messages: История диалога (без последнего вопроса HR)
            hr_question: Вопрос HR, на который нужно ответить
            candidate_profile: Профиль кандидата
            options: Опции симуляции
            
        Returns:
            Optional[str]: Сгенерированный ответ или None в случае ошибки
        """
        try:
            # Форматируем историю диалога (исключаем последний вопрос HR)
            formatted_history = format_dialog_history(dialog_messages[:-1])
            
            # Строим промпт для кандидата
            prompt = self.prompt_builder.build_candidate_prompt(
                formatted_resume=formatted_resume,
                formatted_vacancy=formatted_vacancy,
                formatted_history=formatted_history,
                hr_question=hr_question,
                candidate_profile=candidate_profile,
                options=options
            )
            
            if options.log_detailed_prompts:
                self._log.debug(f"Candidate промпт:\n{prompt.system[:200]}...")
            
            # Простая схема для текстового ответа
            class _TextOnly(BaseModel):
                text: str

            # Генерируем ответ с настройками для кандидата
            result = await self._llm.generate_structured(
                prompt=prompt,
                schema=_TextOnly,
                temperature=getattr(options, 'temperature_candidate', 0.8),
                max_tokens=getattr(options, 'max_tokens_per_message', 2500)
            )
            
            answer = (result.text or "").strip() if result else None
            self._log.debug(f"Сгенерирован ответ кандидата длиной {len(answer) if answer else 0} символов")
            return answer
            
        except Exception as e:
            self._log.error(f"Ошибка генерации ответа кандидата: {e}")
            return None
    
    def _select_question_type_for_round(self,
                                       round_number: int,
                                       candidate_profile: CandidateProfile,
                                       dialog_messages: List[DialogMessage]) -> QuestionType:
        """Выбирает тип вопроса для текущего раунда.
        
        Args:
            round_number: Номер раунда
            candidate_profile: Профиль кандидата
            dialog_messages: История диалога
            
        Returns:
            QuestionType: Выбранный тип вопроса
        """
        # Получаем возможные типы для раунда
        possible_types = get_question_types_for_round(round_number)
        
        # Получаем уже использованные типы
        used_types = {
            msg.question_type for msg in dialog_messages 
            if msg.speaker == "HR" and msg.question_type
        }
        
        # Добавляем leadership вопросы для управленцев
        if (candidate_profile.management_experience and 
            candidate_profile.detected_level in [candidate_profile.detected_level.SENIOR, candidate_profile.detected_level.LEAD] and
            QuestionType.LEADERSHIP not in used_types and
            round_number >= 4):
            possible_types.append(QuestionType.LEADERSHIP)
        
        # Убираем уже использованные типы
        available_types = [qt for qt in possible_types if qt not in used_types]
        
        if not available_types:
            return QuestionType.FINAL
        
        # Выбираем первый доступный (в будущем можно добавить более умную логику)
        selected_type = available_types[0]
        self._log.debug(f"Выбран тип вопроса для раунда {round_number}: {selected_type.value}")
        return selected_type
    
    def _evaluate_response_quality(self,
                                  answer: str,
                                  question_type: QuestionType,
                                  candidate_profile: CandidateProfile) -> int:
        """Оценивает качество ответа кандидата.
        
        Args:
            answer: Ответ кандидата
            question_type: Тип заданного вопроса
            candidate_profile: Профиль кандидата
            
        Returns:
            int: Оценка от 1 до 5
        """
        if not answer:
            return 1
        
        score = 3  # Базовая оценка
        
        # Оценка по длине ответа
        if len(answer) < 50:
            score -= 1  # Слишком короткий
        elif len(answer) > 200:
            score += 1  # Детальный ответ
        
        # Бонусы за конкретику
        concrete_keywords = ['например', 'конкретно', 'проект', 'результат', 'опыт', 'решил', 'сделал']
        if any(keyword in answer.lower() for keyword in concrete_keywords):
            score += 1
        
        # Проверка STAR структуры для поведенческих вопросов
        if question_type == QuestionType.BEHAVIORAL_STAR:
            star_keywords = ['ситуация', 'задача', 'действие', 'результат', 'проблема', 'решение']
            star_matches = sum(1 for kw in star_keywords if kw in answer.lower())
            if star_matches >= 3:
                score += 1
        
        # Корректировка по уровню кандидата
        if candidate_profile.detected_level == CandidateLevel.JUNIOR:
            score += 0.5  # Более мягкая оценка для junior
        elif candidate_profile.detected_level == CandidateLevel.LEAD:
            score -= 0.5  # Более строгая оценка для lead
        
        final_score = max(1, min(5, round(score)))
        self._log.debug(f"Оценка ответа: {final_score}/5 (длина: {len(answer)}, тип: {question_type.value})")
        return final_score
    
    async def _generate_assessment(self,
                                  resume: ResumeInfo,
                                  vacancy: VacancyInfo,
                                  dialog_messages: List[DialogMessage],
                                  candidate_profile: CandidateProfile,
                                  options: InterviewSimulationOptions) -> InterviewAssessment:
        """Генерирует профессиональную оценку результатов интервью.
        
        Args:
            resume: Исходная информация о резюме
            vacancy: Исходная информация о вакансии
            dialog_messages: Полная история диалога
            candidate_profile: Профиль кандидата
            options: Опции симуляции
            
        Returns:
            InterviewAssessment: Детальная оценка интервью
        """
        self._log.info("Генерируем профессиональную оценку интервью")
        
        if not options.enable_assessment:
            # Создаем базовую оценку без LLM анализа
            return self._create_basic_assessment(dialog_messages, candidate_profile)
        
        try:
            # Используем Assessment Engine для детальной оценки
            assessment = await self.assessment_engine.generate_comprehensive_assessment(
                resume_data=self._convert_resume_to_dict(resume),
                vacancy_data=self._convert_vacancy_to_dict(vacancy),
                dialog_messages=dialog_messages,
                candidate_profile=candidate_profile
            )
            
            self._log.info(f"Оценка сгенерирована: {assessment.overall_recommendation}")
            return assessment
            
        except Exception as e:
            self._log.error(f"Ошибка генерации оценки: {e}")
            # Возвращаем базовую оценку в случае ошибки
            return self._create_basic_assessment(dialog_messages, candidate_profile)
    
    async def _generate_feedback(self,
                                assessment: InterviewAssessment,
                                candidate_profile: CandidateProfile) -> Dict[str, str]:
        """Генерирует текстовые рекомендации на основе оценки.
        
        Args:
            assessment: Детальная оценка интервью
            candidate_profile: Профиль кандидата
            
        Returns:
            Dict[str, str]: Словарь с текстовыми рекомендациями
        """
        try:
            feedback = await self.assessment_engine.generate_detailed_feedback(
                assessment, candidate_profile
            )
            return feedback
            
        except Exception as e:
            self._log.error(f"Ошибка генерации обратной связи: {e}")
            # Создаем базовую обратную связь
            return self._create_basic_feedback(assessment, candidate_profile)
    
    def _apply_options_to_config(self,
                                config: InterviewConfiguration,
                                options: InterviewSimulationOptions) -> InterviewConfiguration:
        """Применяет настройки из опций к конфигурации интервью.
        
        Args:
            config: Базовая конфигурация
            options: Опции с пользовательскими настройками
            
        Returns:
            InterviewConfiguration: Обновленная конфигурация
        """
        # Переопределяем параметры из опций
        if options.target_rounds != 5:  # Если отличается от дефолта
            config.target_rounds = options.target_rounds
        
        if options.difficulty_level != "medium":
            config.difficulty_level = options.difficulty_level
        
        if options.focus_areas:
            config.focus_areas = options.focus_areas
        
        config.include_behavioral = options.include_behavioral
        config.include_technical = options.include_technical
        
        self._log.debug(f"Конфигурация обновлена: {config.target_rounds} раундов, {config.difficulty_level}")
        return config
    
    def _create_basic_assessment(self,
                                dialog_messages: List[DialogMessage],
                                candidate_profile: CandidateProfile) -> InterviewAssessment:
        """Создает базовую оценку без использования LLM.
        
        Args:
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            
        Returns:
            InterviewAssessment: Базовая оценка
        """
        # Вычисляем среднее качество ответов
        candidate_scores = [
            msg.response_quality for msg in dialog_messages
            if msg.speaker == "Candidate" and msg.response_quality is not None
        ]
        avg_quality = sum(candidate_scores) / len(candidate_scores) if candidate_scores else 3.0
        
        # Определяем рекомендацию
        if avg_quality >= 4.0:
            recommendation = "hire"
        elif avg_quality >= 3.0:
            recommendation = "conditional_hire"
        else:
            recommendation = "reject"
        
        # Создаем базовые оценки компетенций
        competency_scores = [
            CompetencyScore(
                area=CompetencyArea.TECHNICAL_EXPERTISE,
                score=max(1, min(5, round(avg_quality))),
                evidence=["Базовая оценка на основе качества ответов"],
                improvement_notes="Требуется детальная оценка"
            ),
            CompetencyScore(
                area=CompetencyArea.COMMUNICATION,
                score=max(1, min(5, round(avg_quality))),
                evidence=["Базовая оценка на основе качества ответов"],
                improvement_notes="Требуется детальная оценка"
            )
        ]
        
        return InterviewAssessment(
            overall_recommendation=recommendation,
            competency_scores=competency_scores,
            strengths=["Участие в интервью", "Готовность отвечать на вопросы"],
            weaknesses=["Требуется детальная оценка"],
            red_flags=[],
            cultural_fit_score=3
        )
    
    def _create_basic_feedback(self,
                              assessment: InterviewAssessment,
                              candidate_profile: CandidateProfile) -> Dict[str, str]:
        """Создает базовую обратную связь.
        
        Args:
            assessment: Оценка интервью
            candidate_profile: Профиль кандидата
            
        Returns:
            Dict[str, str]: Базовая обратная связь
        """
        avg_score = assessment.average_competency_score
        
        hr_assessment = f"Кандидат уровня {candidate_profile.detected_level.value} показал результат {avg_score:.1f}/5. Рекомендация: {assessment.overall_recommendation}."
        
        performance_analysis = f"Сильные стороны: {', '.join(assessment.strengths[:2])}. "
        if assessment.weaknesses:
            performance_analysis += f"Области для развития: {', '.join(assessment.weaknesses[:2])}."
        
        improvement_recommendations = "Продолжайте развивать профессиональные навыки. Готовьтесь к техническим интервью более детально."
        
        return {
            'hr_assessment': hr_assessment,
            'performance_analysis': performance_analysis,
            'improvement_recommendations': improvement_recommendations
        }
    
    def _create_simulation_metadata(self,
                                   dialog_messages: List[DialogMessage],
                                   candidate_profile: CandidateProfile,
                                   interview_config: InterviewConfiguration,
                                   options: InterviewSimulationOptions) -> Dict[str, Any]:
        """Создает метаданные симуляции.
        
        Args:
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            interview_config: Конфигурация интервью
            options: Опции симуляции
            
        Returns:
            Dict[str, Any]: Метаданные симуляции
        """
        return {
            'rounds_completed': len(dialog_messages) // 2,
            'total_rounds_planned': interview_config.target_rounds,
            'model_used': self._llm.default_model if hasattr(self._llm, 'default_model') else 'unknown',
            'candidate_level': candidate_profile.detected_level.value,
            'candidate_role': candidate_profile.detected_role.value,
            'difficulty_level': interview_config.difficulty_level,
            'question_types_covered': [
                msg.question_type.value for msg in dialog_messages 
                if msg.speaker == "HR" and msg.question_type
            ],
            'average_response_quality': sum(
                msg.response_quality for msg in dialog_messages
                if msg.speaker == "Candidate" and msg.response_quality is not None
            ) / max(1, len([
                msg for msg in dialog_messages 
                if msg.speaker == "Candidate" and msg.response_quality is not None
            ])),
            'feature_version': self.get_supported_versions()[0],
            'assessment_enabled': options.enable_assessment
        }
    
    def _extract_candidate_name(self, resume: ResumeInfo) -> str:
        """Извлекает имя кандидата из резюме.
        
        Args:
            resume: Информация о резюме
            
        Returns:
            str: Имя кандидата
        """
        first_name = getattr(resume, 'first_name', '')
        last_name = getattr(resume, 'last_name', '')
        name = f"{first_name} {last_name}".strip()
        return name if name else "Кандидат"
    
    def _create_company_context(self, vacancy: VacancyInfo) -> str:
        """Создает контекст компании для симуляции.
        
        Args:
            vacancy: Информация о вакансии
            
        Returns:
            str: Контекст компании
        """
        position = getattr(vacancy, 'name', 'IT позиция')
        employer = getattr(vacancy, 'employer', 'Компания')
        
        if hasattr(employer, 'name'):
            employer_name = employer.name
        else:
            employer_name = str(employer) if employer else 'Компания'
        
        return f"Интервью на позицию {position} в компании {employer_name}"
    
    def _convert_resume_to_dict(self, resume: ResumeInfo) -> Dict[str, Any]:
        """Конвертирует ResumeInfo в словарь для Assessment Engine.
        
        Args:
            resume: Информация о резюме
            
        Returns:
            Dict[str, Any]: Словарь с данными резюме
        """
        # Простая конвертация через model_dump если доступно
        if hasattr(resume, 'model_dump'):
            return resume.model_dump()
        elif hasattr(resume, 'dict'):
            return resume.dict()
        else:
            # Ручная конвертация основных полей
            return {
                'first_name': getattr(resume, 'first_name', ''),
                'last_name': getattr(resume, 'last_name', ''),
                'title': getattr(resume, 'title', ''),
                'skills': getattr(resume, 'skills', ''),
                'skill_set': getattr(resume, 'skill_set', []),
                'experience': getattr(resume, 'experience', []),
                'education': getattr(resume, 'education', {}),
                'salary': getattr(resume, 'salary', {}),
                'total_experience': getattr(resume, 'total_experience', {})
            }
    
    def _convert_vacancy_to_dict(self, vacancy: VacancyInfo) -> Dict[str, Any]:
        """Конвертирует VacancyInfo в словарь для Assessment Engine.
        
        Args:
            vacancy: Информация о вакансии
            
        Returns:
            Dict[str, Any]: Словарь с данными вакансии
        """
        # Простая конвертация через model_dump если доступно
        if hasattr(vacancy, 'model_dump'):
            return vacancy.model_dump()
        elif hasattr(vacancy, 'dict'):
            return vacancy.dict()
        else:
            # Ручная конвертация основных полей
            return {
                'name': getattr(vacancy, 'name', ''),
                'description': getattr(vacancy, 'description', ''),
                'employer': getattr(vacancy, 'employer', {}),
                'key_skills': getattr(vacancy, 'key_skills', []),
                'experience': getattr(vacancy, 'experience', {}),
                'employment': getattr(vacancy, 'employment', {}),
                'schedule': getattr(vacancy, 'schedule', {}),
                'salary': getattr(vacancy, 'salary', '')
            }
    
    def _merge_with_defaults(self, options: BaseLLMOptions) -> InterviewSimulationOptions:
        """Сливает пользовательские опции с настройками по умолчанию.
        
        Args:
            options: Пользовательские опции
            
        Returns:
            InterviewSimulationOptions: Объединенные опции
        """
        # Конвертируем BaseLLMOptions в InterviewSimulationOptions если нужно
        if isinstance(options, InterviewSimulationOptions):
            merged_options = options
        else:
            # Создаем InterviewSimulationOptions из базовых опций
            merged_options = InterviewSimulationOptions(
                prompt_version=options.prompt_version,
                temperature=options.temperature,
                max_tokens=options.max_tokens,
                quality_checks=options.quality_checks
            )
        
        # Объединяем с настройками по умолчанию
        default_options = self.settings.default_options
        
        # Обновляем только те поля, которые не были заданы пользователем
        for field_name, field_value in default_options.dict().items():
            if not hasattr(merged_options, field_name) or getattr(merged_options, field_name) is None:
                setattr(merged_options, field_name, field_value)
        
        self._log.debug(f"Опции объединены: {merged_options.target_rounds} раундов, сложность {merged_options.difficulty_level}")
        return merged_options
    
    def get_feature_name(self) -> str:
        """Возвращает название фичи."""
        return self.settings.feature_name
    
    def get_supported_versions(self) -> list[str]:
        """Возвращает поддерживаемые версии фичи."""
        return [self.settings.feature_version]
    
    def format_for_output(self, result: InterviewSimulation) -> str:
        """Форматирует результат для текстового вывода.
        
        Args:
            result: Результат симуляции интервью
            
        Returns:
            str: Отформатированный текст
        """
        return f"""=== СИМУЛЯЦИЯ ИНТЕРВЬЮ ===

Позиция: {result.position_title}
Кандидат: {result.candidate_name}
Уровень: {result.candidate_profile.detected_level.value}
Роль: {result.candidate_profile.detected_role.value}

=== РЕЗУЛЬТАТ ===
Раундов проведено: {result.total_rounds_completed}
Средняя оценка ответов: {result.average_response_quality:.1f}/5
Рекомендация: {result.assessment.overall_recommendation}

=== ОЦЕНКА HR ===
{result.hr_assessment}

=== АНАЛИЗ ВЫСТУПЛЕНИЯ ===
{result.candidate_performance_analysis}

=== РЕКОМЕНДАЦИИ ===
{result.improvement_recommendations}
"""


# Создание экземпляра Assessment Engine адаптированного для нашей архитектуры
class ProfessionalAssessmentEngine:
    """Адаптированная система профессиональной оценки для LLM Features Framework."""
    
    def __init__(self):
        """Инициализация системы оценки."""
        self.logger = logger.getChild("AssessmentEngine")
    
    async def generate_comprehensive_assessment(self,
                                              resume_data: Dict[str, Any],
                                              vacancy_data: Dict[str, Any],
                                              dialog_messages: List[DialogMessage],
                                              candidate_profile: CandidateProfile) -> InterviewAssessment:
        """Генерирует всестороннюю оценку интервью.
        
        Примечание: Это упрощенная версия для первой итерации.
        В будущем здесь будет полная интеграция с оригинальным Assessment Engine.
        
        Args:
            resume_data: Данные резюме в формате словаря
            vacancy_data: Данные вакансии в формате словаря
            dialog_messages: История диалога
            candidate_profile: Профиль кандидата
            
        Returns:
            InterviewAssessment: Детальная оценка
        """
        self.logger.info("Генерируем комплексную оценку интервью")
        
        # Базовая оценка на основе качества ответов
        candidate_responses = [
            msg for msg in dialog_messages 
            if msg.speaker == "Candidate" and msg.response_quality is not None
        ]
        
        if not candidate_responses:
            # Если нет ответов для оценки
            return self._create_default_assessment()
        
        avg_quality = sum(msg.response_quality for msg in candidate_responses) / len(candidate_responses)
        
        # Создаем оценки компетенций
        competency_scores = self._assess_competencies(dialog_messages, candidate_profile, avg_quality)
        
        # Определяем общую рекомендацию
        recommendation = self._determine_recommendation(competency_scores, avg_quality)
        
        # Анализируем сильные и слабые стороны
        strengths, weaknesses = self._analyze_strengths_weaknesses(dialog_messages, candidate_profile)
        
        # Ищем красные флаги
        red_flags = self._detect_red_flags(dialog_messages)
        
        # Оцениваем культурное соответствие
        cultural_fit = self._assess_cultural_fit(dialog_messages, avg_quality)
        
        assessment = InterviewAssessment(
            overall_recommendation=recommendation,
            competency_scores=competency_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            red_flags=red_flags,
            cultural_fit_score=cultural_fit
        )
        
        self.logger.info(f"Оценка создана: {recommendation}, средний балл: {assessment.average_competency_score:.1f}")
        return assessment
    
    async def generate_detailed_feedback(self,
                                        assessment: InterviewAssessment,
                                        candidate_profile: CandidateProfile) -> Dict[str, str]:
        """Генерирует детальную обратную связь.
        
        Args:
            assessment: Оценка интервью
            candidate_profile: Профиль кандидата
            
        Returns:
            Dict[str, str]: Обратная связь
        """
        avg_score = assessment.average_competency_score
        
        # HR Assessment
        hr_assessment = f"Кандидат уровня {candidate_profile.detected_level.value} в роли {candidate_profile.detected_role.value.replace('_', ' ')} "
        hr_assessment += f"показал {'отличный' if avg_score >= 4.5 else 'хороший' if avg_score >= 3.5 else 'удовлетворительный' if avg_score >= 2.5 else 'слабый'} результат. "
        hr_assessment += f"Рекомендация: {assessment.overall_recommendation}."
        
        # Performance Analysis
        performance_analysis = f"Во время интервью кандидат продемонстрировал следующие сильные стороны: {', '.join(assessment.strengths[:3])}. "
        if assessment.weaknesses:
            performance_analysis += f"Области требующие развития: {', '.join(assessment.weaknesses[:2])}. "
        performance_analysis += f"Культурное соответствие оценено в {assessment.cultural_fit_score}/5 баллов."
        
        # Improvement Recommendations
        recommendations = []
        if avg_score < 4.0:
            recommendations.append("Улучшите навыки презентации своего опыта с конкретными примерами")
        if any('technical' in cs.area.value for cs in assessment.competency_scores if cs.score < 4):
            recommendations.append("Углубите технические знания в ключевых областях")
        if any('communication' in cs.area.value for cs in assessment.competency_scores if cs.score < 4):
            recommendations.append("Развивайте навыки структурированного изложения мыслей")
        if not recommendations:
            recommendations.append("Продолжайте развивать лидерские качества и экспертизу")
        
        improvement_recommendations = ". ".join(recommendations) + "."
        
        return {
            'hr_assessment': hr_assessment,
            'performance_analysis': performance_analysis,
            'improvement_recommendations': improvement_recommendations
        }
    
    def _assess_competencies(self,
                            dialog_messages: List[DialogMessage],
                            candidate_profile: CandidateProfile,
                            avg_quality: float) -> List[CompetencyScore]:
        """Оценивает компетенции на основе диалога."""
        
        competencies = default_settings.level_competencies.get(
            candidate_profile.detected_level,
            [CompetencyArea.TECHNICAL_EXPERTISE, CompetencyArea.COMMUNICATION]
        )
        
        scores = []
        for competency in competencies:
            # Базовая оценка на основе средней качества ответов
            base_score = max(1, min(5, round(avg_quality)))
            
            # Модификация по типу компетенции
            if competency == CompetencyArea.TECHNICAL_EXPERTISE:
                # Ищем технические вопросы
                tech_responses = [
                    msg for msg in dialog_messages
                    if msg.speaker == "Candidate" and any(
                        prev_msg.question_type == QuestionType.TECHNICAL_SKILLS
                        for prev_msg in dialog_messages[max(0, dialog_messages.index(msg)-1):dialog_messages.index(msg)]
                        if prev_msg.speaker == "HR"
                    )
                ]
                if tech_responses:
                    tech_avg = sum(msg.response_quality or 3 for msg in tech_responses) / len(tech_responses)
                    base_score = max(1, min(5, round(tech_avg)))
            
            scores.append(CompetencyScore(
                area=competency,
                score=base_score,
                evidence=[f"Анализ ответов кандидата в интервью"],
                improvement_notes=f"Продолжайте развивать навыки в области {competency.value}"
            ))
        
        return scores
    
    def _determine_recommendation(self, competency_scores: List[CompetencyScore], avg_quality: float) -> str:
        """Определяет общую рекомендацию."""
        avg_competency = sum(cs.score for cs in competency_scores) / len(competency_scores) if competency_scores else avg_quality
        
        if avg_competency >= 4.0:
            return "hire"
        elif avg_competency >= 3.0:
            return "conditional_hire"
        else:
            return "reject"
    
    def _analyze_strengths_weaknesses(self, dialog_messages: List[DialogMessage], candidate_profile: CandidateProfile) -> Tuple[List[str], List[str]]:
        """Анализирует сильные и слабые стороны."""
        
        candidate_responses = [msg for msg in dialog_messages if msg.speaker == "Candidate"]
        avg_quality = sum(msg.response_quality or 3 for msg in candidate_responses) / len(candidate_responses) if candidate_responses else 3
        
        strengths = ["Готовность к диалогу", "Профессиональная коммуникация"]
        weaknesses = []
        
        if avg_quality >= 4.0:
            strengths.extend(["Детальные ответы", "Хорошее понимание вопросов"])
        elif avg_quality < 3.0:
            weaknesses.extend(["Краткие ответы", "Недостаток конкретных примеров"])
        
        if candidate_profile.years_of_experience and candidate_profile.years_of_experience > 3:
            strengths.append("Богатый профессиональный опыт")
        
        if not weaknesses:
            weaknesses.append("Возможности для дальнейшего развития")
        
        return strengths, weaknesses
    
    def _detect_red_flags(self, dialog_messages: List[DialogMessage]) -> List[str]:
        """Выявляет красные флаги."""
        
        red_flags = []
        candidate_responses = [msg for msg in dialog_messages if msg.speaker == "Candidate"]
        
        # Проверяем слишком короткие ответы
        short_responses = [msg for msg in candidate_responses if len(msg.message) < 50]
        if len(short_responses) >= len(candidate_responses) * 0.5:
            red_flags.append("Большинство ответов слишком краткие")
        
        # Проверяем качество ответов
        low_quality_responses = [msg for msg in candidate_responses if (msg.response_quality or 3) <= 2]
        if len(low_quality_responses) >= len(candidate_responses) * 0.4:
            red_flags.append("Низкое качество ответов")
        
        return red_flags
    
    def _assess_cultural_fit(self, dialog_messages: List[DialogMessage], avg_quality: float) -> int:
        """Оценивает культурное соответствие."""
        
        # Базовая оценка на основе качества коммуникации
        base_score = max(1, min(5, round(avg_quality)))
        
        # Ищем вопросы о культуре и мотивации
        culture_responses = [
            msg for msg in dialog_messages
            if msg.speaker == "Candidate" and any(
                prev_msg.question_type in [QuestionType.MOTIVATION, QuestionType.CULTURE_FIT]
                for prev_msg in dialog_messages[max(0, dialog_messages.index(msg)-1):dialog_messages.index(msg)]
                if prev_msg.speaker == "HR"
            )
        ]
        
        if culture_responses:
            culture_avg = sum(msg.response_quality or 3 for msg in culture_responses) / len(culture_responses)
            base_score = max(1, min(5, round(culture_avg)))
        
        return base_score
    
    def _create_default_assessment(self) -> InterviewAssessment:
        """Создает дефолтную оценку."""
        
        return InterviewAssessment(
            overall_recommendation="conditional_hire",
            competency_scores=[
                CompetencyScore(
                    area=CompetencyArea.COMMUNICATION,
                    score=3,
                    evidence=["Участие в интервью"],
                    improvement_notes="Требуется дополнительная оценка"
                )
            ],
            strengths=["Готовность к интервью"],
            weaknesses=["Недостаточно данных для полной оценки"],
            red_flags=[],
            cultural_fit_score=3
        )
