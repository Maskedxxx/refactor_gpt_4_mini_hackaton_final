# src/llm_interview_checklist/service.py
# --- agent_meta ---
# role: llm-interview-checklist-service
# owner: @backend
# contract: Основной генератор профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - LLMInterviewChecklistGenerator (AbstractLLMGenerator[ProfessionalInterviewChecklist])
# --- /agent_meta ---

from typing import Dict, List, Optional, Any

from src.llm_features.base.generator import AbstractLLMGenerator
from src.llm_features.base.options import BaseLLMOptions
from src.parsing.llm.prompt import Prompt
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo

from .models import ProfessionalInterviewChecklist, CandidateLevel, VacancyType, CompanyFormat
from .options import InterviewChecklistOptions
from .config import settings
from .formatter import format_resume_for_interview_prep, format_vacancy_for_interview_prep
from .prompts.templates import create_professional_interview_checklist_prompt
from .prompts.mappings import (
    detect_vacancy_type_from_description,
    analyze_candidate_level,
    detect_company_format,
)


class LLMInterviewChecklistGenerator(AbstractLLMGenerator[ProfessionalInterviewChecklist]):
    """
    Генератор профессионального чек-листа подготовки к интервью.
    Использует HR-экспертизу для создания персонализированных рекомендаций.
    """

    def __init__(self, *args, **kwargs):
        """Инициализация генератора с настройками по умолчанию."""
        super().__init__(*args, **kwargs)
        self.settings = settings

    async def _build_prompt(
        self,
        resume: ResumeInfo,
        vacancy: VacancyInfo,
        options: InterviewChecklistOptions,
    ) -> Prompt:
        """
        Создает промпт для генерации профессионального чек-листа подготовки к интервью.
        
        Args:
            resume: Информация о резюме кандидата
            vacancy: Информация о целевой вакансии
            options: Опции генерации чек-листа
            
        Returns:
            Сформированный промпт для LLM
        """
        # Конвертируем модели в словари для форматтеров
        resume_dict = resume.model_dump() if hasattr(resume, 'model_dump') else resume.dict()
        vacancy_dict = vacancy.model_dump() if hasattr(vacancy, 'model_dump') else vacancy.dict()
        
        # Форматируем данные для анализа
        formatted_resume = format_resume_for_interview_prep(resume_dict)
        formatted_vacancy = format_vacancy_for_interview_prep(vacancy_dict)
        
        # Анализируем контекст кандидата и вакансии
        candidate_level = self._determine_candidate_level(resume_dict, options)
        vacancy_type = self._determine_vacancy_type(vacancy_dict, options)
        company_format = self._determine_company_format(vacancy_dict, options)
        
        # Создаем промпт с персонализацией
        prompt_template = create_professional_interview_checklist_prompt(
            formatted_resume=formatted_resume,
            formatted_vacancy=formatted_vacancy,
            candidate_level=candidate_level,
            vacancy_type=vacancy_type,
            company_format=company_format,
            extra_context=options.extra_context,
        )
        
        return prompt_template.render({})

    async def _call_llm(
        self,
        prompt: Prompt,
        options: InterviewChecklistOptions,
    ) -> ProfessionalInterviewChecklist:
        """
        Вызывает LLM для генерации структурированного чек-листа.
        
        Args:
            prompt: Подготовленный промпт
            options: Опции генерации
            
        Returns:
            Сгенерированный профессиональный чек-лист
        """
        # Используем structured output для получения модели ProfessionalInterviewChecklist
        result = await self._llm.generate_structured(
            prompt=prompt,
            schema=ProfessionalInterviewChecklist,
            temperature=options.temperature,
            model_name=options.model_name or self.settings.model_name,
        )
        
        return result

    def _merge_with_defaults(self, options: Optional[InterviewChecklistOptions]) -> InterviewChecklistOptions:
        """
        Объединяет пользовательские опции с настройками по умолчанию.
        
        Args:
            options: Пользовательские опции или None
            
        Returns:
            Объединенные опции с применением дефолтов
        """
        if options is None:
            options = InterviewChecklistOptions()

        # Применяем дефолты из настроек
        if options.model_name is None:
            options.model_name = self.settings.model_name
        
        if options.temperature is None:
            options.temperature = self.settings.temperature
            
        if options.prompt_version is None:
            options.prompt_version = self.settings.prompt_version
            
        if options.preparation_time_available is None:
            options.preparation_time_available = self.settings.default_preparation_time

        return options

    def get_feature_name(self) -> str:
        """Возвращает имя фичи для регистрации."""
        return "interview_checklist"

    def get_supported_versions(self) -> List[str]:
        """Возвращает список поддерживаемых версий промптов."""
        return ["v1"]

    def _determine_candidate_level(
        self, 
        resume_dict: Dict[str, Any], 
        options: InterviewChecklistOptions
    ) -> CandidateLevel:
        """Определяет уровень кандидата для персонализации."""
        # Если есть явная подсказка в опциях, используем её
        if options.candidate_level_hint:
            try:
                return CandidateLevel(options.candidate_level_hint.upper())
            except ValueError:
                pass  # Игнорируем неверные значения и переходим к автоопределению
        
        # Автоматическое определение уровня
        experience_data = resume_dict.get('experience', [])
        total_experience = resume_dict.get('total_experience', 0)
        
        # Преобразуем total_experience в месяцы если это словарь
        if isinstance(total_experience, dict):
            total_months = total_experience.get('months', 0) or 0
        else:
            total_months = total_experience or 0
            
        return analyze_candidate_level(experience_data, total_months)

    def _determine_vacancy_type(
        self, 
        vacancy_dict: Dict[str, Any], 
        options: InterviewChecklistOptions
    ) -> VacancyType:
        """Определяет тип вакансии для адаптации подготовки."""
        title = vacancy_dict.get('name', '')
        description = vacancy_dict.get('description', '')
        
        detected_type = detect_vacancy_type_from_description(title, description)
        return detected_type or VacancyType.OTHER

    def _determine_company_format(
        self, 
        vacancy_dict: Dict[str, Any], 
        options: InterviewChecklistOptions
    ) -> CompanyFormat:
        """Определяет формат компании для адаптации стиля подготовки."""
        # Если есть явная подсказка в опциях, используем её
        if options.company_format_hint:
            try:
                return CompanyFormat(options.company_format_hint.upper())
            except ValueError:
                pass  # Игнорируем неверные значения и переходим к автоопределению
        
        # Автоматическое определение формата
        company_name = vacancy_dict.get('company_name', '')
        description = vacancy_dict.get('description', '')
        
        return detect_company_format(company_name, description)