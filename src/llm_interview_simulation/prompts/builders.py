# src/llm_interview_simulation/prompts/builders.py
# --- agent_meta ---
# role: interview-simulation-prompt-builders
# owner: @backend
# contract: Строители промптов для HR и кандидата в симуляции интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - InterviewPromptBuilder (основной строитель)
#   - HRPromptBuilder (промпты для HR-менеджера)
#   - CandidatePromptBuilder (промпты для кандидата)
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Any, List, Tuple
from abc import ABC, abstractmethod

from src.utils import get_logger
from src.parsing.llm.prompt import Prompt

from ..models import (
    DialogMessage, CandidateProfile, InterviewConfiguration, 
    QuestionType, CandidateLevel, ITRole
)
from ..options import InterviewSimulationOptions
from ..config import app_config
from .template_engine import render_template

logger = get_logger(__name__)


class BasePromptBuilder(ABC):
    """Базовый класс для строителей промптов симуляции интервью."""
    
    def __init__(self):
        """Инициализация строителя."""
        self.logger = logger.getChild(self.__class__.__name__)
    
    @abstractmethod
    def build_prompt(self, context: Dict[str, Any]) -> Prompt:
        """Строит промпт на основе контекста.
        
        Args:
            context: Контекст для построения промпта
            
        Returns:
            Prompt: Готовый промпт для LLM
        """
        pass


class HRPromptBuilder(BasePromptBuilder):
    """Строитель промптов для HR-менеджера.
    
    Создает адаптивные промпты для генерации вопросов HR-менеджера
    в зависимости от уровня кандидата, типа вопроса и хода интервью.
    """
    
    def __init__(self):
        super().__init__()
        # Конфигурация промптов из YAML (может быть пустой)
        self._cfg = app_config.get('prompts', {}).get('hr', {})

    def build_prompt(self, context: Dict[str, Any]) -> Prompt:
        """Строит промпт для генерации вопроса HR-менеджера.
        
        Args:
            context: Контекст содержащий:
                - formatted_resume: str
                - formatted_vacancy: str  
                - formatted_history: str
                - round_number: int
                - question_type: QuestionType
                - candidate_profile: CandidateProfile
                - interview_config: InterviewConfiguration
                - options: InterviewSimulationOptions
                
        Returns:
            Prompt: Промпт для генерации вопроса HR
        """
        self.logger.debug(f"Строим HR промпт для раунда {context.get('round_number')}")
        
        # Извлекаем данные из контекста
        formatted_resume = context['formatted_resume']
        formatted_vacancy = context['formatted_vacancy']
        formatted_history = context['formatted_history']
        round_number = context['round_number']
        question_type = context['question_type']
        candidate_profile = context['candidate_profile']
        interview_config = context['interview_config']
        options = context.get('options', {})
        
        # Если YAML-конфиг доступен — используем его, иначе дефолтная логика ниже
        if self._cfg:
            level_value = candidate_profile.detected_level.value
            role_value = candidate_profile.detected_role.value
            hr_personality = getattr(options, 'hr_personality', 'neutral')

            personas = self._cfg.get('personas', {})
            level_approaches = self._cfg.get('level_approaches', {})
            qinstr_map = self._cfg.get('question_instructions', {})
            personalities = self._cfg.get('personalities', {})
            role_guidance_map = self._cfg.get('role_guidance', {})
            round_instr = self._cfg.get('round_instructions', {})

            hr_persona = personas.get(level_value, "Профессиональный HR-специалист")
            level_adaptation = level_approaches.get(level_value, "")
            question_instructions_tpl = qinstr_map.get(question_type.value, "")
            personality_instructions = personalities.get(hr_personality, "")
            role_guidance = role_guidance_map.get(role_value, "")
            round_specific_instruction = (
                round_instr.get(str(round_number))
                or round_instr.get('default')
                or "Задай следующий вопрос, основываясь на предыдущих ответах кандидата."
            )

            # Рендерим вложенные шаблоны (например, role_value внутри question_instructions)
            question_instructions = render_template(question_instructions_tpl, {
                'role_value': role_value,
                'level_value': level_value,
            })

            focus_areas = [area.value for area in interview_config.focus_areas[:3]]
            context_map = {
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
                'question_instructions': question_instructions,
                'personality_instructions': personality_instructions,
                'role_guidance': role_guidance,
                'round_specific_instruction': round_specific_instruction,
            }

            system_template = self._cfg.get('system_template', '')
            system_prompt = render_template(system_template, context_map)
            user_prompt = self._cfg.get('user_prompt', '') or (
                "Задай следующий вопрос, основываясь на контексте интервью и предыдущих ответах. Ответь только текстом вопроса без дополнительных комментариев."
            )

            return Prompt(system=system_prompt, user=user_prompt)

        # --- Fallback: прежняя дефолтная логика, если нет YAML ---
        hr_persona = self._get_hr_persona(candidate_profile.detected_level)
        question_instructions = self._get_question_type_instructions(
            question_type, candidate_profile
        )
        level_adaptation = self._get_level_specific_approach(candidate_profile.detected_level)
        role_guidance = self._get_role_specific_guidance(candidate_profile.detected_role)
        hr_personality = getattr(options, 'hr_personality', 'neutral')
        personality_instructions = self._get_personality_instructions(hr_personality)

        system_prompt = f"""# Роль: {hr_persona}

Ты — опытный HR-менеджер IT-компании с 10+ лет опыта проведения технических интервью.

{level_adaptation}

{personality_instructions}

## Контекст интервью:

{formatted_resume}

{formatted_vacancy}

{formatted_history}

## Текущая ситуация:
- Раунд интервью: {round_number} из {interview_config.target_rounds}
- Тип вопроса: {question_type.value}
- Профиль кандидата: {candidate_profile.detected_level.value} {candidate_profile.detected_role.value}
- Фокус интервью: {', '.join([area.value for area in interview_config.focus_areas[:3]])}

## Специфичные инструкции для этого раунда:

{question_instructions}

{role_guidance}

## Профессиональные принципы интервьюирования:

1. **Структурированный подход**: Используй методику STAR для поведенческих вопросов
2. **Глубина vs. Деликатность**: Докапывайся до сути, но дружелюбно
3. **Конкретика**: Требуй примеры и детали, не принимай общие ответы
4. **Баланс**: Оценивай как hard skills, так и soft skills
5. **Уважение**: Поддерживай профессиональный, но теплый тон
6. **Адаптивность**: Корректируй сложность в зависимости от ответов кандидата

## Требования к вопросу:
- ОДИН конкретный вопрос (2-3 предложения максимум)
- Соответствует уровню кандидата и типу раунда
- Позволяет глубоко оценить компетенцию
- Профессиональный, но дружелюбный тон
- На русском языке
- Избегай повторения уже заданных вопросов

{self._get_round_specific_instruction(round_number)}"""

        user_prompt = "Задай следующий вопрос, основываясь на контексте интервью и предыдущих ответах. Ответь только текстом вопроса без дополнительных комментариев."

        return Prompt(system=system_prompt, user=user_prompt)
    
    def _get_hr_persona(self, level: CandidateLevel) -> str:
        """Возвращает персону HR в зависимости от уровня кандидата."""
        personas = {
            CandidateLevel.JUNIOR: "Поддерживающий наставник и строгий оценщик базовых навыков",
            CandidateLevel.MIDDLE: "Профессиональный эксперт, проверяющий глубину знаний",
            CandidateLevel.SENIOR: "Опытный лидер, оценивающий экспертизу и лидерский потенциал",
            CandidateLevel.LEAD: "Senior Partner, проводящий стратегическое интервью на равных"
        }
        return personas.get(level, "Профессиональный HR-специалист")
    
    def _get_question_type_instructions(self, question_type: QuestionType, 
                                      candidate_profile: CandidateProfile) -> str:
        """Возвращает инструкции для конкретного типа вопроса."""
        
        instructions = {
            QuestionType.INTRODUCTION: """
**ЗНАКОМСТВО И ВВЕДЕНИЕ**
- Поприветствуй кандидата тепло и профессионально
- Кратко представь себя и процесс интервью
- Задай открытый вопрос о кандидате или его мотивации
- Цель: снизить напряжение, оценить коммуникативные навыки
""",
            
            QuestionType.TECHNICAL_SKILLS: f"""
**ПРОВЕРКА ТЕХНИЧЕСКИХ НАВЫКОВ**
- Фокусируйся на ключевых технологиях для роли {candidate_profile.detected_role.value}
- Спрашивай о конкретном опыте, а не теоретических знаниях
- Проси примеры реального использования технологий
- Проверяй понимание best practices и подходов к решению задач
- Цель: оценить глубину и применимость технических знаний
""",
            
            QuestionType.EXPERIENCE_DEEP_DIVE: """
**ГЛУБОКИЙ АНАЛИЗ ОПЫТА**
- Выбери один значимый проект из резюме
- Используй воронку вопросов: контекст → задача → действия → результат
- Проверяй роль кандидата, его конкретный вклад в проект
- Интересуйся сложностями и способами их решения
- Цель: понять реальный уровень и стиль работы
""",
            
            QuestionType.BEHAVIORAL_STAR: """
**ПОВЕДЕНЧЕСКИЕ ВОПРОСЫ (STAR)**
- Задавай ситуационные вопросы: "Расскажите о случае, когда..."
- Требуй структуры STAR: Ситуация → Задача → Действие → Результат
- Фокусируйся на сложных/конфликтных ситуациях
- Проверяй навыки работы в команде, решения проблем
- Цель: оценить soft skills и стиль решения проблем
""",
            
            QuestionType.PROBLEM_SOLVING: """
**РЕШЕНИЕ ПРОБЛЕМ**
- Предложи гипотетическую рабочую ситуацию или кейс
- Попроси объяснить подход к решению пошагово
- Оценивай логику мышления, а не правильность ответа
- Интересуйся альтернативными подходами
- Цель: понять аналитические способности и креативность
""",
            
            QuestionType.MOTIVATION: """
**МОТИВАЦИЯ И ЦЕЛИ**
- Выясни причины смены работы и интерес к компании
- Спроси о долгосрочных планах развития
- Проверь знание о компании и позиции
- Узнай о карьерных амбициях и ожиданиях
- Цель: оценить искренность мотивации и культурное соответствие
""",
            
            QuestionType.CULTURE_FIT: """
**СООТВЕТСТВИЕ КУЛЬТУРЕ**
- Спроси о предпочитаемом стиле работы и команды
- Выясни ценности и принципы в работе
- Обсуди ожидания от рабочей среды
- Проверь готовность к изменениям и адаптивность
- Цель: определить культурное соответствие
""",
            
            QuestionType.LEADERSHIP: """
**ЛИДЕРСКИЕ КАЧЕСТВА**
- Спроси о опыте управления людьми/проектами
- Выясни стиль руководства и подход к конфликтам
- Проверь навыки развития команды и делегирования
- Интересуйся примерами принятия сложных решений
- Цель: оценить лидерский потенциал и управленческие навыки
""",
            
            QuestionType.FINAL: """
**ЗАВЕРШАЮЩИЕ ВОПРОСЫ**
- Предложи кандидату задать вопросы о компании/роли
- Уточни ожидания по зарплате и срокам выхода
- Поблагодари за интервью
- Дай возможность добавить что-то важное
- Цель: закрыть оставшиеся вопросы, показать уважение
"""
        }
        
        return instructions.get(question_type, "Задай релевантный вопрос по теме интервью.")
    
    def _get_level_specific_approach(self, level: CandidateLevel) -> str:
        """Возвращает подход, специфичный для уровня кандидата."""
        
        approaches = {
            CandidateLevel.JUNIOR: """
**Подход для Junior кандидата:**
Помни: кандидат может нервничать. Будь поддерживающим, но не снижай планку.
Фокусируйся на потенциале, обучаемости и базовых навыках.
Приводи примеры и давай подсказки при необходимости.
Оценивай готовность учиться и развиваться.
""",
            
            CandidateLevel.MIDDLE: """
**Подход для Middle кандидата:**
Ожидай уверенные ответы и конкретные примеры.
Проверяй глубину знаний и способность работать самостоятельно.
Оценивай готовность брать на себя больше ответственности.
Интересуйся опытом решения нестандартных задач.
""",
            
            CandidateLevel.SENIOR: """
**Подход для Senior кандидата:**
Веди диалог как с экспертом. Задавай сложные вопросы.
Проверяй способность принимать архитектурные решения.
Оценивай потенциал менторства и технического лидерства.
Интересуйся влиянием на команду и процессы.
""",
            
            CandidateLevel.LEAD: """
**Подход для Lead кандидата:**
Общайся как с равным. Фокусируйся на стратегическом мышлении.
Проверяй опыт управления людьми и процессами.
Оценивай способность влиять на техническое направление компании.
Интересуйся видением развития продукта и команды.
"""
        }
        
        return approaches.get(level, "Адаптируй подход под уровень кандидата.")
    
    def _get_role_specific_guidance(self, role: ITRole) -> str:
        """Возвращает рекомендации, специфичные для IT-роли."""
        
        guidance = {
            ITRole.DEVELOPER: """
**Специфика для разработчиков:**
- Проверяй понимание архитектурных паттернов и принципов SOLID
- Спрашивай о code review, тестировании, CI/CD процессах
- Интересуйся подходом к отладке и оптимизации кода
- Проверяй знание современных практик разработки
""",
            
            ITRole.DATA_SCIENTIST: """
**Специфика для Data Scientists:**
- Фокусируйся на понимании бизнес-задач через данные
- Проверяй знание ML pipeline и model validation
- Спрашивай о работе с большими данными и stakeholders
- Интересуйся подходом к feature engineering и выбору моделей
""",
            
            ITRole.QA: """
**Специфика для QA:**
- Проверяй понимание разных видов тестирования
- Спрашивай о построении тест-планов и автоматизации
- Интересуйся подходом к поиску и документированию багов
- Проверяй знание инструментов тестирования
""",
            
            ITRole.DEVOPS: """
**Специфика для DevOps:**
- Фокусируйся на понимании инфраструктуры и мониторинга
- Проверяй опыт с containerization и orchestration
- Спрашивай о подходе к обеспечению надежности системы
- Интересуйся опытом с облачными платформами
""",
            
            ITRole.PROJECT_MANAGER: """
**Специфика для Project Managers:**
- Проверяй знание методологий (Agile, Scrum, Kanban)
- Спрашивай о управлении рисками и stakeholders
- Интересуйся подходом к планированию и контролю
- Проверяй навыки коммуникации с техническими командами
"""
        }
        
        return guidance.get(role, "Учитывай специфику IT-роли в вопросах.")
    
    def _get_personality_instructions(self, personality: str) -> str:
        """Возвращает инструкции по стилю поведения HR."""
        
        personalities = {
            'supportive': """
**Стиль: Поддерживающий**
- Будь особенно дружелюбным и ободряющим
- Помогай кандидату раскрыться, давай подсказки
- Фокусируйся на сильных сторонах
- Создавай комфортную атмосферу
""",
            'neutral': """
**Стиль: Нейтральный (профессиональный)**
- Поддерживай баланс между дружелюбием и профессионализмом
- Будь объективным в оценках
- Давай кандидату возможность проявить себя
- Соблюдай структуру интервью
""",
            'challenging': """
**Стиль: Строгий (challenging)**
- Задавай более сложные и провокационные вопросы
- Проверяй кандидата на стрессоустойчивость
- Будь требовательным к деталям и примерам
- Не принимай поверхностные ответы
"""
        }
        
        return personalities.get(personality, personalities['neutral'])
    
    def _get_round_specific_instruction(self, round_number: int) -> str:
        """Возвращает специфичную инструкцию для раунда."""
        
        if round_number == 1:
            return "Начни интервью с приветствия и первого вопроса. Создай комфортную атмосферу."
        else:
            return "Задай следующий вопрос, основываясь на предыдущих ответах кандидата."


class CandidatePromptBuilder(BasePromptBuilder):
    """Строитель промптов для кандидата.
    
    Создает промпты для генерации ответов кандидата на вопросы HR-менеджера
    с учетом уровня кандидата и его профиля.
    """
    
    def __init__(self):
        super().__init__()
        self._cfg = app_config.get('prompts', {}).get('candidate', {})

    def build_prompt(self, context: Dict[str, Any]) -> Prompt:
        """Строит промпт для генерации ответа кандидата.
        
        Args:
            context: Контекст содержащий:
                - formatted_resume: str
                - formatted_vacancy: str
                - formatted_history: str
                - hr_question: str
                - candidate_profile: CandidateProfile
                - options: InterviewSimulationOptions
                
        Returns:
            Prompt: Промпт для генерации ответа кандидата
        """
        self.logger.debug("Строим промпт для ответа кандидата")
        
        # Извлекаем данные из контекста
        formatted_resume = context['formatted_resume']
        formatted_vacancy = context['formatted_vacancy']
        formatted_history = context['formatted_history']
        hr_question = context['hr_question']
        candidate_profile = context['candidate_profile']
        options = context.get('options', {})
        
        # Если YAML-конфиг доступен — используем его, иначе fallback
        if self._cfg:
            level_value = candidate_profile.detected_level.value
            role_value = candidate_profile.detected_role.value
            confidence = getattr(options, 'candidate_confidence', 'medium')

            base_styles = self._cfg.get('base_styles', {})
            conf_mod = self._cfg.get('confidence_modifiers', {})
            role_tips = self._cfg.get('role_tips', {})

            response_style = (base_styles.get(level_value, '') + conf_mod.get(confidence, ''))
            role_specific_tips = role_tips.get(role_value, '')

            context_map = {
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

            system_template = self._cfg.get('system_template', '')
            system_prompt = render_template(system_template, context_map)
            user_prompt = self._cfg.get('user_prompt', '') or (
                "Ответь на вопрос HR-менеджера как кандидат на позицию. Ответь только текстом ответа без дополнительных комментариев."
            )

            return Prompt(system=system_prompt, user=user_prompt)

        # --- Fallback: прежняя дефолтная логика, если нет YAML ---
        response_style = self._get_candidate_response_style(
            candidate_profile.detected_level,
            getattr(options, 'candidate_confidence', 'medium')
        )
        role_specific_tips = self._get_role_specific_tips(candidate_profile.detected_role)

        system_prompt = f"""# Роль: {candidate_profile.detected_level.value.title()} {candidate_profile.detected_role.value.replace('_', ' ').title()}

Ты — IT-специалист уровня {candidate_profile.detected_level.value}, который проходит интервью на позицию, 
описанную в вакансии. Ты хорошо подготовился и очень заинтересован в получении этой работы.

## Твоя информация (резюме):

{formatted_resume}

## Информация о целевой позиции:

{formatted_vacancy}

## История интервью:

{formatted_history}

## Твой стиль ответа:

{response_style}

{role_specific_tips}

## Принципы ответа:

1. **Основывайся на резюме**: Используй только информацию из своего профиля, не выдумывай опыт
2. **STAR для поведенческих вопросов**: Структурируй ответы как Ситуация → Задача → Действие → Результат  
3. **Конкретика**: Приводи числа, технологии, реальные примеры из опыта
4. **Честность**: Если не знаешь чего-то — признайся, но покажи готовность изучать
5. **Связь с вакансией**: Подчеркивай соответствие требованиям позиции
6. **Профессионализм**: Говори уверенно, но без высокомерия
7. **Естественность**: Отвечай как живой человек, а не как робот

## Требования к ответу:
- Отвечай только на заданный вопрос
- 3-6 предложений (в зависимости от сложности вопроса)
- Профессиональная лексика соответствующего уровня
- На русском языке
- Не задавай встречных вопросов в этом ответе (если не просят)
- Покажи энтузиазм и заинтересованность

## Текущий вопрос от HR-менеджера:

"{hr_question}"

Ответь профессионально и по существу, основываясь на своем опыте из резюме."""

        user_prompt = "Ответь на вопрос HR-менеджера как кандидат на позицию. Ответь только текстом ответа без дополнительных комментариев."

        return Prompt(system=system_prompt, user=user_prompt)
    
    def _get_candidate_response_style(self, level: CandidateLevel, confidence: str) -> str:
        """Определяет стиль ответов в зависимости от уровня кандидата и уверенности."""
        
        base_styles = {
            CandidateLevel.JUNIOR: """
- Показывай энтузиазм и готовность учиться
- Признавай ограничения опыта, но демонстрируй потенциал
- Приводи примеры из учебы, pet-проектов, стажировок
- Задавай уточняющие вопросы при сложных темах
- Подчеркивай мотивацию к развитию
""",
            
            CandidateLevel.MIDDLE: """
- Демонстрируй уверенность в своих навыках
- Приводи конкретные примеры из рабочих проектов
- Показывай понимание бизнес-контекста задач
- Упоминай опыт работы в команде и с разными технологиями
- Проявляй готовность к новым вызовам
""",
            
            CandidateLevel.SENIOR: """
- Говори как эксперт в своей области
- Демонстрируй системное мышление и архитектурный подход
- Упоминай опыт принятия технических решений
- Показывай понимание влияния решений на бизнес
- Проявляй лидерские качества
""",
            
            CandidateLevel.LEAD: """
- Общайся как технический лидер
- Фокусируйся на управлении людьми и процессами
- Демонстрируй стратегическое мышление
- Показывай опыт влияния на техническое направление
- Говори о развитии команды и продукта
"""
        }
        
        base_style = base_styles.get(level, base_styles[CandidateLevel.MIDDLE])
        
        # Модификация по уровню уверенности
        confidence_modifiers = {
            'low': "\n- Будь немного менее уверенным, проявляй некоторую неуверенность\n- Чаще упоминай желание учиться",
            'medium': "\n- Поддерживай баланс между уверенностью и скромностью",
            'high': "\n- Будь очень уверенным в своих способностях\n- Проявляй амбициозность и нацеленность на результат"
        }
        
        return base_style + confidence_modifiers.get(confidence, confidence_modifiers['medium'])
    
    def _get_role_specific_tips(self, role: ITRole) -> str:
        """Возвращает специфичные советы для IT-роли."""
        
        tips = {
            ITRole.DEVELOPER: """
## Специфика для разработчика:
- Упоминай конкретные технологии и фреймворки из опыта
- Говори о code review, тестировании, архитектурных решениях
- Демонстрируй понимание best practices разработки
- Приводи примеры оптимизации и рефакторинга кода
""",
            
            ITRole.DATA_SCIENTIST: """
## Специфика для Data Scientist:
- Говори о работе с данными и ML моделями
- Упоминай business impact и метрики моделей
- Демонстрируй понимание data pipeline и feature engineering
- Приводи примеры решения аналитических задач
""",
            
            ITRole.QA: """
## Специфика для QA:
- Говори о подходах к тестированию и quality assurance
- Упоминай инструменты автоматизации и test frameworks
- Демонстрируй понимание SDLC и bug lifecycle
- Приводи примеры найденных критичных багов
""",
            
            ITRole.DEVOPS: """
## Специфика для DevOps:
- Говори об инфраструктуре, CI/CD, мониторинге
- Упоминай облачные платформы и контейнеризацию
- Демонстрируй понимание reliability и scalability
- Приводи примеры автоматизации процессов
"""
        }
        
        return tips.get(role, "## Общие советы:\n- Адаптируй ответы под специфику своей IT-роли")


class InterviewPromptBuilder:
    """Основной строитель промптов для симуляции интервью.
    
    Координирует работу HR и Candidate prompt builders для создания
    полного диалога интервью.
    """
    
    def __init__(self):
        """Инициализация основного строителя."""
        self.hr_builder = HRPromptBuilder()
        self.candidate_builder = CandidatePromptBuilder()
        self.logger = logger.getChild("InterviewPromptBuilder")
    
    def build_hr_prompt(self, 
                       formatted_resume: str,
                       formatted_vacancy: str,
                       formatted_history: str,
                       round_number: int,
                       question_type: QuestionType,
                       candidate_profile: CandidateProfile,
                       interview_config: InterviewConfiguration,
                       options: InterviewSimulationOptions) -> Prompt:
        """Строит промпт для HR-менеджера.
        
        Returns:
            Prompt: Готовый промпт для генерации вопроса HR
        """
        self.logger.debug(f"Строим HR промпт для раунда {round_number}, тип: {question_type.value}")
        
        context = {
            'formatted_resume': formatted_resume,
            'formatted_vacancy': formatted_vacancy,
            'formatted_history': formatted_history,
            'round_number': round_number,
            'question_type': question_type,
            'candidate_profile': candidate_profile,
            'interview_config': interview_config,
            'options': options
        }
        
        return self.hr_builder.build_prompt(context)
    
    def build_candidate_prompt(self,
                              formatted_resume: str,
                              formatted_vacancy: str, 
                              formatted_history: str,
                              hr_question: str,
                              candidate_profile: CandidateProfile,
                              options: InterviewSimulationOptions) -> Prompt:
        """Строит промпт для кандидата.
        
        Returns:
            Prompt: Готовый промпт для генерации ответа кандидата
        """
        self.logger.debug("Строим промпт для ответа кандидата")
        
        context = {
            'formatted_resume': formatted_resume,
            'formatted_vacancy': formatted_vacancy,
            'formatted_history': formatted_history,
            'hr_question': hr_question,
            'candidate_profile': candidate_profile,
            'options': options
        }
        
        return self.candidate_builder.build_prompt(context)
