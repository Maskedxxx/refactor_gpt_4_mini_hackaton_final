# src/llm_interview_simulation/prompts/builders.py
# --- agent_meta ---
# role: interview-simulation-prompt-builders
# owner: @backend
# contract: Строители промптов для HR и кандидата в симуляции интервью (только YAML, без fallbacks)
# last_reviewed: 2025-08-19
# interfaces:
#   - InterviewPromptBuilder (основной строитель)
#   - HRPromptBuilder (промпты для HR-менеджера)
#   - CandidatePromptBuilder (промпты для кандидата)
# --- /agent_meta ---

"""
Строители промптов (HR и Кандидат) без дублирования текста: только YAML-конфиг.
Вся динамика и маппинг переменных сосредоточены в prompts/context.py.
"""

from __future__ import annotations

from typing import Dict, Any
from abc import ABC, abstractmethod

from src.utils import get_logger
from src.parsing.llm.prompt import Prompt

from ..models import CandidateProfile, InterviewConfiguration, QuestionType
from ..options import InterviewSimulationOptions
from ..config import app_config
from .template_engine import render_template
from .context import build_hr_context, build_candidate_context

logger = get_logger(__name__)


class BasePromptBuilder(ABC):
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)

    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> Prompt:  # pragma: no cover
        pass


class HRPromptBuilder(BasePromptBuilder):
    def __init__(self):
        super().__init__()
        self._cfg = app_config.get('prompts', {}).get('hr', {})

    def build_prompt(self, context: Dict[str, Any]) -> Prompt:
        self.logger.debug(f"Строим HR промпт для раунда {context.get('round_number')}")

        context_map = build_hr_context(
            formatted_resume=context['formatted_resume'],
            formatted_vacancy=context['formatted_vacancy'],
            formatted_history=context['formatted_history'],
            round_number=context['round_number'],
            question_type=context['question_type'],
            candidate_profile=context['candidate_profile'],
            interview_config=context['interview_config'],
            options=context.get('options', {}),
            cfg=self._cfg,
        )
        # Рендер подшаблона инструкций типа вопроса,
        # чтобы поддерживать вложенные плейсхолдеры (роль/уровень)
        qinstr_map = self._cfg.get('question_instructions', {})
        qt = context['question_type']
        qtpl = qinstr_map.get(qt.value, '')
        context_map['question_instructions'] = render_template(
            qtpl, {'role_value': context_map['role_value'], 'level_value': context_map['level_value']}
        )

        system_template = self._cfg.get('system_template', '')
        user_prompt = self._cfg.get('user_prompt', '')
        return Prompt(system=render_template(system_template, context_map), user=user_prompt)


class CandidatePromptBuilder(BasePromptBuilder):
    def __init__(self):
        super().__init__()
        self._cfg = app_config.get('prompts', {}).get('candidate', {})

    def build_prompt(self, context: Dict[str, Any]) -> Prompt:
        self.logger.debug("Строим промпт для ответа кандидата")

        context_map = build_candidate_context(
            formatted_resume=context['formatted_resume'],
            formatted_history=context['formatted_history'],
            hr_question=context['hr_question'],
            candidate_profile=context['candidate_profile'],
            options=context.get('options', {}),
            cfg=self._cfg,
        )
        system_template = self._cfg.get('system_template', '')
        user_prompt = self._cfg.get('user_prompt', '')
        return Prompt(system=render_template(system_template, context_map), user=user_prompt)


class InterviewPromptBuilder:
    def __init__(self):
        self.hr_builder = HRPromptBuilder()
        self.candidate_builder = CandidatePromptBuilder()
        self.logger = logger.getChild("InterviewPromptBuilder")

    def build_hr_prompt(
        self,
        *,
        formatted_resume: str,
        formatted_vacancy: str,
        formatted_history: str,
        round_number: int,
        question_type: QuestionType,
        candidate_profile: CandidateProfile,
        interview_config: InterviewConfiguration,
        options: InterviewSimulationOptions,
    ) -> Prompt:
        self.logger.debug(f"Строим HR промпт для раунда {round_number}, тип: {question_type.value}")
        context = {
            'formatted_resume': formatted_resume,
            'formatted_vacancy': formatted_vacancy,
            'formatted_history': formatted_history,
            'round_number': round_number,
            'question_type': question_type,
            'candidate_profile': candidate_profile,
            'interview_config': interview_config,
            'options': options,
        }
        return self.hr_builder.build_prompt(context)

    def build_candidate_prompt(
        self,
        *,
        formatted_resume: str,
        formatted_vacancy: str,
        formatted_history: str,
        hr_question: str,
        candidate_profile: CandidateProfile,
        options: InterviewSimulationOptions,
    ) -> Prompt:
        self.logger.debug("Строим промпт для ответа кандидата")
        context = {
            'formatted_resume': formatted_resume,
            'formatted_vacancy': formatted_vacancy,
            'formatted_history': formatted_history,
            'hr_question': hr_question,
            'candidate_profile': candidate_profile,
            'options': options,
        }
        return self.candidate_builder.build_prompt(context)
