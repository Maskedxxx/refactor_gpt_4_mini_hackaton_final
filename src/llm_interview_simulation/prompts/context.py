# src/llm_interview_simulation/prompts/context.py
# --- agent_meta ---
# role: interview-simulation-prompt-context
# owner: @backend
# contract: Единое построение контекста переменных для Jinja-шаблонов промптов
# last_reviewed: 2025-08-19
# interfaces:
#   - build_hr_context(...) -> dict
#   - build_candidate_context(...) -> dict
# --- /agent_meta ---

from __future__ import annotations

from typing import Any, Dict

from ..models import CandidateProfile, InterviewConfiguration, QuestionType
from ..options import InterviewSimulationOptions


def build_hr_context(
    *,
    formatted_resume: str,
    formatted_vacancy: str,
    formatted_history: str,
    round_number: int,
    question_type: QuestionType,
    candidate_profile: CandidateProfile,
    interview_config: InterviewConfiguration,
    options: InterviewSimulationOptions,
    cfg: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    level_value = candidate_profile.detected_level.value
    role_value = candidate_profile.detected_role.value
    hr_personality = getattr(options, 'hr_personality', 'neutral')

    cfg = cfg or {}
    personas = cfg.get('personas', {})
    level_approaches = cfg.get('level_approaches', {})
    personalities = cfg.get('personalities', {})
    role_guidance_map = cfg.get('role_guidance', {})
    round_instr = cfg.get('round_instructions', {})

    hr_persona = personas.get(level_value, "Профессиональный HR-специалист")
    level_adaptation = level_approaches.get(level_value, "")
    personality_instructions = personalities.get(hr_personality, "")
    role_guidance = role_guidance_map.get(role_value, "")
    round_specific_instruction = (
        round_instr.get(str(round_number))
        or round_instr.get('default')
        or "Задай следующий вопрос, основываясь на предыдущих ответах кандидата."
    )

    focus_areas = [area.value for area in interview_config.focus_areas[:3]]
    return {
        'formatted_resume': formatted_resume,
        'formatted_vacancy': formatted_vacancy,
        'formatted_history': formatted_history,
        'round_number': round_number,
        'target_rounds': interview_config.target_rounds,
        'question_type_value': question_type.value,
        'candidate_profile': candidate_profile,
        'role_value': role_value,
        'role_title': role_value.replace('_', ' ').title(),
        'level_value': level_value,
        'level_title': level_value.title(),
        'focus_areas': focus_areas,
        'focus_areas_str': ', '.join(focus_areas),
        'hr_persona': hr_persona,
        'level_adaptation': level_adaptation,
        'personality_instructions': personality_instructions,
        'role_guidance': role_guidance,
        'round_specific_instruction': round_specific_instruction,
    }


def build_candidate_context(
    *,
    formatted_resume: str,
    formatted_history: str,
    hr_question: str,
    candidate_profile: CandidateProfile,
    options: InterviewSimulationOptions,
    cfg: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    level_value = candidate_profile.detected_level.value
    role_value = candidate_profile.detected_role.value
    confidence = getattr(options, 'candidate_confidence', 'medium')

    cfg = cfg or {}
    base_styles = cfg.get('base_styles', {})
    conf_mod = cfg.get('confidence_modifiers', {})
    role_tips = cfg.get('role_tips', {})

    response_style = (base_styles.get(level_value, '') + conf_mod.get(confidence, ''))
    role_specific_tips = role_tips.get(role_value, '')

    return {
        'formatted_resume': formatted_resume,
        'formatted_history': formatted_history,
        'hr_question': hr_question,
        'role_value': role_value,
        'role_title': role_value.replace('_', ' ').title(),
        'level_value': level_value,
        'level_title': level_value.title(),
        'response_style': response_style,
        'role_specific_tips': role_specific_tips,
    }

