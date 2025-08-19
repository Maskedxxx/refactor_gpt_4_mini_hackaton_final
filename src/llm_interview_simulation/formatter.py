# src/llm_interview_simulation/formatter.py
# --- agent_meta ---
# role: interview-simulation-formatter
# owner: @backend
# contract: Адаптированные форматтеры для преобразования ResumeInfo/VacancyInfo в формат для симуляции интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - format_resume_for_interview_simulation()
#   - format_vacancy_for_interview_simulation()
#   - SmartCandidateAnalyzer (анализ профиля)
#   - InterviewConfigurationBuilder (построение конфигурации)
# --- /agent_meta ---

from __future__ import annotations

import re
from typing import Dict, List, Any, Optional, Tuple

from src.utils import get_logger
from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo

from .models import (
    CandidateLevel, ITRole, CandidateProfile, InterviewConfiguration, 
    QuestionType, CompetencyArea, DialogMessage
)
from .config import default_settings

logger = get_logger(__name__)


class SmartCandidateAnalyzer:
    """Интеллектуальный анализатор профиля кандидата на основе ResumeInfo.
    
    Адаптированная версия для работы с унифицированными моделями данных
    LLM Features Framework вместо сырых данных из оригинального кода.
    """
    
    def __init__(self):
        """Инициализация анализатора с настройками по умолчанию."""
        self.role_keywords = default_settings.role_keywords
        self.tech_categories = default_settings.tech_categories
        self.logger = logger.getChild("CandidateAnalyzer")
    
    def analyze_candidate_profile(self, resume: ResumeInfo) -> CandidateProfile:
        """Анализирует резюме и создает профиль кандидата.
        
        Args:
            resume: Структурированная информация о резюме
            
        Returns:
            CandidateProfile: Профиль кандидата с автоопределенными характеристиками
        """
        self.logger.info("Начинаем анализ профиля кандидата")
        
        # Определяем уровень кандидата
        level = self._determine_candidate_level(resume)
        self.logger.debug(f"Определен уровень кандидата: {level.value}")
        
        # Определяем IT-роль
        role = self._determine_it_role(resume)
        self.logger.debug(f"Определена IT-роль: {role.value}")
        
        # Извлекаем годы опыта
        years_exp = self._extract_years_of_experience(resume)
        self.logger.debug(f"Опыт работы: {years_exp} лет")
        
        # Извлекаем ключевые технологии
        technologies = self._extract_key_technologies(resume)
        self.logger.debug(f"Ключевые технологии: {technologies[:5]}...")  # Первые 5 для лога
        
        # Анализируем образование
        education = self._analyze_education(resume)
        
        # Извлекаем предыдущие компании
        companies = self._extract_companies(resume)
        
        # Проверяем опыт управления
        has_management = self._check_management_experience(resume)
        self.logger.debug(f"Управленческий опыт: {has_management}")
        
        profile = CandidateProfile(
            detected_level=level,
            detected_role=role,
            years_of_experience=years_exp,
            key_technologies=technologies,
            education_level=education,
            previous_companies=companies,
            management_experience=has_management
        )
        
        self.logger.info(f"Профиль кандидата создан: {level.value} {role.value}")
        return profile
    
    def _determine_candidate_level(self, resume: ResumeInfo) -> CandidateLevel:
        """Определяет уровень кандидата на основе опыта и навыков."""
        
        # Получаем общий опыт в месяцах из модели ResumeInfo
        total_exp_months = 0
        
        # ResumeInfo.total_experience может быть строкой или объектом
        if hasattr(resume, 'total_experience') and resume.total_experience:
            if isinstance(resume.total_experience, dict):
                total_exp_months = resume.total_experience.get('months', 0)
            elif isinstance(resume.total_experience, str):
                # Пытаемся извлечь числа из строки
                numbers = re.findall(r'\d+', resume.total_experience)
                if numbers:
                    total_exp_months = int(numbers[0]) * 12  # Предполагаем что это годы
        
        # Также проверяем опыт работы
        if hasattr(resume, 'experience') and resume.experience:
            # Считаем примерный опыт по количеству мест работы и позициям
            exp_count = len(resume.experience) if isinstance(resume.experience, list) else 1
            # Эвристика: каждое место работы = примерно 2 года
            estimated_months = exp_count * 24
            total_exp_months = max(total_exp_months, estimated_months)
        
        years_exp = total_exp_months / 12 if total_exp_months > 0 else 0
        
        # Определяем уровень по опыту
        if years_exp < 1:
            level = CandidateLevel.JUNIOR
        elif years_exp < 3:
            level = CandidateLevel.MIDDLE
        elif years_exp < 6:
            level = CandidateLevel.SENIOR
        else:
            level = CandidateLevel.LEAD
        
        self.logger.debug(f"Опыт {years_exp:.1f} лет -> уровень {level.value}")
        return level
    
    def _determine_it_role(self, resume: ResumeInfo) -> ITRole:
        """Определяет IT-роль кандидата на основе навыков и опыта."""
        
        # Собираем текст для анализа из различных полей ResumeInfo
        text_to_analyze = []
        
        # Заголовок резюме
        if hasattr(resume, 'title') and resume.title:
            text_to_analyze.append(resume.title.lower())
        
        # Навыки из skill_set
        if hasattr(resume, 'skill_set') and resume.skill_set:
            if isinstance(resume.skill_set, list):
                text_to_analyze.extend([skill.lower() for skill in resume.skill_set])
            else:
                text_to_analyze.append(str(resume.skill_set).lower())
        
        # Описание навыков
        if hasattr(resume, 'skills') and resume.skills:
            text_to_analyze.append(str(resume.skills).lower())
        
        # Опыт работы
        if hasattr(resume, 'experience') and resume.experience:
            for exp in resume.experience:
                if hasattr(exp, 'position') and exp.position:
                    text_to_analyze.append(exp.position.lower())
                if hasattr(exp, 'description') and exp.description:
                    text_to_analyze.append(exp.description.lower())
        
        # Профессиональные роли
        if hasattr(resume, 'professional_roles') and resume.professional_roles:
            for role in resume.professional_roles:
                if hasattr(role, 'name') and role.name:
                    text_to_analyze.append(role.name.lower())
        
        full_text = ' '.join(text_to_analyze)
        self.logger.debug(f"Анализируем текст длиной {len(full_text)} символов для определения роли")
        
        # Подсчитываем совпадения для каждой роли
        role_scores = {}
        for role, keywords in self.role_keywords.items():
            score = sum(1 for keyword in keywords if keyword in full_text)
            role_scores[role] = score
            if score > 0:
                self.logger.debug(f"Роль {role.value}: {score} совпадений")
        
        # Возвращаем роль с наивысшим скором
        if role_scores:
            best_role = max(role_scores, key=role_scores.get)
            if role_scores[best_role] > 0:
                return best_role
        
        self.logger.debug("Не удалось определить специфичную роль, возвращаем OTHER")
        return ITRole.OTHER
    
    def _extract_years_of_experience(self, resume: ResumeInfo) -> Optional[int]:
        """Извлекает количество лет опыта из ResumeInfo."""
        
        # Пытаемся получить из total_experience
        if hasattr(resume, 'total_experience') and resume.total_experience:
            if isinstance(resume.total_experience, dict):
                months = resume.total_experience.get('months', 0)
                return round(months / 12) if months > 0 else None
            elif isinstance(resume.total_experience, str):
                # Ищем числа в строке
                numbers = re.findall(r'\d+', resume.total_experience)
                if numbers:
                    return int(numbers[0])  # Первое число как годы
        
        # Альтернативно считаем по опыту работы
        if hasattr(resume, 'experience') and resume.experience:
            return len(resume.experience) * 2  # Эвристика: 2 года на место работы
        
        return None
    
    def _extract_key_technologies(self, resume: ResumeInfo) -> List[str]:
        """Извлекает ключевые технологии из резюме."""
        
        technologies = set()
        
        # Из skill_set
        if hasattr(resume, 'skill_set') and resume.skill_set:
            skill_list = resume.skill_set if isinstance(resume.skill_set, list) else [resume.skill_set]
            for skill in skill_list:
                skill_lower = str(skill).lower()
                # Проверяем во всех категориях технологий
                for category, techs in self.tech_categories.items():
                    for tech in techs:
                        if tech in skill_lower:
                            technologies.add(str(skill))  # Добавляем оригинальное название
        
        # Из текстового описания навыков
        if hasattr(resume, 'skills') and resume.skills:
            skills_text = str(resume.skills).lower()
            for category, techs in self.tech_categories.items():
                for tech in techs:
                    if tech in skills_text:
                        technologies.add(tech.title())
        
        result = list(technologies)[:15]  # Ограничиваем количество
        self.logger.debug(f"Извлечено {len(result)} технологий")
        return result
    
    def _analyze_education(self, resume: ResumeInfo) -> Optional[str]:
        """Анализирует уровень образования."""
        
        if hasattr(resume, 'education') and resume.education:
            # Пытаемся получить уровень образования
            if hasattr(resume.education, 'level') and resume.education.level:
                if hasattr(resume.education.level, 'name'):
                    return resume.education.level.name
                else:
                    return str(resume.education.level)
            
            # Альтернативно ищем в primary образовании
            if hasattr(resume.education, 'primary') and resume.education.primary:
                if isinstance(resume.education.primary, list) and resume.education.primary:
                    first_edu = resume.education.primary[0]
                    if hasattr(first_edu, 'name'):
                        return first_edu.name
        
        return None
    
    def _extract_companies(self, resume: ResumeInfo) -> List[str]:
        """Извлекает список предыдущих компаний."""
        
        companies = []
        if hasattr(resume, 'experience') and resume.experience:
            for exp in resume.experience:
                if hasattr(exp, 'company') and exp.company:
                    company_name = exp.company
                    if company_name and company_name not in companies:
                        companies.append(company_name)
        
        result = companies[:5]  # Ограничиваем количество
        self.logger.debug(f"Извлечено {len(result)} компаний")
        return result
    
    def _check_management_experience(self, resume: ResumeInfo) -> bool:
        """Проверяет наличие опыта управления."""
        
        management_keywords = [
            'руководитель', 'менеджер', 'lead', 'head', 'manager', 'team lead',
            'управление командой', 'управление проектами', 'scrum master'
        ]
        
        # Проверяем в заголовке
        if hasattr(resume, 'title') and resume.title:
            title_lower = resume.title.lower()
            if any(keyword in title_lower for keyword in management_keywords):
                return True
        
        # Проверяем в опыте работы
        if hasattr(resume, 'experience') and resume.experience:
            for exp in resume.experience:
                if hasattr(exp, 'position') and exp.position:
                    position_lower = exp.position.lower()
                    if any(keyword in position_lower for keyword in management_keywords):
                        return True
                
                if hasattr(exp, 'description') and exp.description:
                    description_lower = exp.description.lower()
                    if any(keyword in description_lower for keyword in management_keywords):
                        return True
        
        return False


class InterviewConfigurationBuilder:
    """Строитель конфигурации интервью на основе профиля кандидата и вакансии."""
    
    def __init__(self):
        """Инициализация строителя."""
        self.logger = logger.getChild("ConfigBuilder")
    
    def build_interview_config(self, candidate_profile: CandidateProfile, 
                             vacancy: VacancyInfo) -> InterviewConfiguration:
        """Создает конфигурацию интервью на основе профиля и вакансии.
        
        Args:
            candidate_profile: Профиль кандидата
            vacancy: Информация о вакансии
            
        Returns:
            InterviewConfiguration: Настроенная конфигурация интервью
        """
        self.logger.info("Создаем конфигурацию интервью")
        
        # Определяем количество раундов
        target_rounds = self._calculate_target_rounds(candidate_profile)
        
        # Определяем приоритетные области
        focus_areas = self._determine_focus_areas(candidate_profile, vacancy)
        
        # Определяем уровень сложности
        difficulty = self._determine_difficulty_level(candidate_profile, vacancy)
        
        config = InterviewConfiguration(
            target_rounds=target_rounds,
            focus_areas=focus_areas,
            include_behavioral=True,
            include_technical=True,
            difficulty_level=difficulty
        )
        
        self.logger.info(f"Конфигурация создана: {target_rounds} раундов, сложность {difficulty}")
        return config
    
    def _calculate_target_rounds(self, profile: CandidateProfile) -> int:
        """Вычисляет оптимальное количество раундов."""
        
        base_rounds = default_settings.level_rounds_mapping.get(profile.detected_level, 5)
        
        # Добавляем раунд для управленцев
        if (profile.management_experience and 
            profile.detected_level in [CandidateLevel.SENIOR, CandidateLevel.LEAD]):
            base_rounds += 1
        
        return min(base_rounds, 7)  # Максимум 7 раундов
    
    def _determine_focus_areas(self, profile: CandidateProfile, 
                             vacancy: VacancyInfo) -> List[CompetencyArea]:
        """Определяет приоритетные области оценки."""
        
        # Получаем базовые компетенции для уровня
        focus_areas = default_settings.level_competencies.get(
            profile.detected_level, 
            default_settings.level_competencies[CandidateLevel.MIDDLE]
        ).copy()
        
        # Добавляем специфичные области для ролей
        if profile.detected_role == ITRole.DATA_SCIENTIST:
            if CompetencyArea.LEARNING_ABILITY not in focus_areas:
                focus_areas.append(CompetencyArea.LEARNING_ABILITY)
        
        if profile.management_experience:
            if CompetencyArea.LEADERSHIP not in focus_areas:
                focus_areas.append(CompetencyArea.LEADERSHIP)
        
        # Всегда добавляем культурное соответствие
        if CompetencyArea.CULTURAL_FIT not in focus_areas:
            focus_areas.append(CompetencyArea.CULTURAL_FIT)
        
        return focus_areas
    
    def _determine_difficulty_level(self, profile: CandidateProfile, 
                                  vacancy: VacancyInfo) -> str:
        """Определяет уровень сложности вопросов."""
        
        # Базовый уровень по профилю кандидата
        level_mapping = {
            CandidateLevel.JUNIOR: "easy",
            CandidateLevel.MIDDLE: "medium",
            CandidateLevel.SENIOR: "hard",
            CandidateLevel.LEAD: "hard"
        }
        
        base_difficulty = level_mapping.get(profile.detected_level, "medium")
        
        # TODO: Можно добавить анализ требований вакансии для корректировки сложности
        # Например, если в вакансии требуется больше опыта чем у кандидата
        
        return base_difficulty


def format_resume_for_interview_simulation(resume: ResumeInfo) -> str:
    """Форматирует ResumeInfo для использования в промптах симуляции интервью.
    
    Args:
        resume: Структурированная информация о резюме
        
    Returns:
        str: Отформатированный текст резюме для промптов
    """
    logger.info("Форматируем резюме для симуляции интервью")
    
    # Создаем анализатор и анализируем профиль
    analyzer = SmartCandidateAnalyzer()
    profile = analyzer.analyze_candidate_profile(resume)
    
    formatted_text = "## ИНФОРМАЦИЯ О КАНДИДАТЕ\n\n"
    
    # Базовая информация
    if hasattr(resume, 'first_name') or hasattr(resume, 'last_name'):
        first_name = getattr(resume, 'first_name', '')
        last_name = getattr(resume, 'last_name', '')
        name = f"{first_name} {last_name}".strip()
        if name:
            formatted_text += f"### Кандидат\n{name}\n\n"
    
    # Автоматически определенный профиль
    formatted_text += "### Профиль кандидата (автоматический анализ)\n"
    formatted_text += f"**Уровень:** {profile.detected_level.value.title()}\n"
    formatted_text += f"**IT-роль:** {profile.detected_role.value.replace('_', ' ').title()}\n"
    if profile.years_of_experience:
        formatted_text += f"**Опыт работы:** {profile.years_of_experience} лет\n"
    if profile.management_experience:
        formatted_text += "**Управленческий опыт:** Да\n"
    formatted_text += "\n"
    
    # Желаемая должность
    if hasattr(resume, 'title') and resume.title:
        formatted_text += "### Специализация кандидата\n"
        formatted_text += f"{resume.title}\n\n"
    
    # Профессиональное описание
    if hasattr(resume, 'skills') and resume.skills:
        formatted_text += "### Профессиональное описание навыков\n"
        formatted_text += f"{resume.skills}\n\n"
    
    # Ключевые технологии (интеллектуальный анализ)
    if profile.key_technologies:
        formatted_text += "### Ключевые технологии кандидата\n"
        for tech in profile.key_technologies:
            formatted_text += f"- {tech}\n"
        formatted_text += "\n"
    
    # Технические навыки из skill_set
    if hasattr(resume, 'skill_set') and resume.skill_set:
        formatted_text += "### Технические навыки кандидата\n"
        skill_list = resume.skill_set if isinstance(resume.skill_set, list) else [resume.skill_set]
        for skill in skill_list:
            formatted_text += f"- {skill}\n"
        formatted_text += "\n"
    
    # Детальный опыт работы
    if hasattr(resume, 'experience') and resume.experience:
        formatted_text += "### Профессиональный опыт кандидата\n"
        for i, exp in enumerate(resume.experience, 1):
            company = getattr(exp, 'company', 'Компания не указана')
            position = getattr(exp, 'position', 'Должность не указана')
            start = getattr(exp, 'start', '')
            end = getattr(exp, 'end', 'по настоящее время')
            description = getattr(exp, 'description', 'Описание отсутствует')
            
            formatted_text += f"#### Опыт работы #{i}: {position} в {company}\n"
            formatted_text += f"Период работы: {start} - {end}\n"
            formatted_text += f"Описание деятельности: {description}\n\n"
    
    # Образование
    if hasattr(resume, 'education') and resume.education:
        formatted_text += "### Образование\n"
        
        if hasattr(resume.education, 'level') and resume.education.level:
            level_name = getattr(resume.education.level, 'name', str(resume.education.level))
            formatted_text += f"**Уровень образования:** {level_name}\n"
        
        if hasattr(resume.education, 'primary') and resume.education.primary:
            edu_list = resume.education.primary if isinstance(resume.education.primary, list) else [resume.education.primary]
            for edu in edu_list:
                name = getattr(edu, 'name', '')
                result = getattr(edu, 'result', '')
                year = getattr(edu, 'year', '')
                if name:
                    formatted_text += f"- {name}"
                    if result:
                        formatted_text += f", {result}"
                    if year:
                        formatted_text += f" ({year})"
                    formatted_text += "\n"
        formatted_text += "\n"
    
    # Зарплатные ожидания
    if hasattr(resume, 'salary') and resume.salary:
        if hasattr(resume.salary, 'amount') and resume.salary.amount:
            currency = getattr(resume.salary, 'currency', 'RUR')
            formatted_text += f"### Зарплатные ожидания\n{resume.salary.amount} {currency}\n\n"
    
    logger.debug(f"Резюме отформатировано, длина текста: {len(formatted_text)} символов")
    return formatted_text


def format_vacancy_for_interview_simulation(vacancy: VacancyInfo) -> str:
    """Форматирует VacancyInfo для использования в промптах симуляции интервью.
    
    Args:
        vacancy: Структурированная информация о вакансии
        
    Returns:
        str: Отформатированный текст вакансии для промптов
    """
    logger.info("Форматируем вакансию для симуляции интервью")
    
    formatted_text = "## ИНФОРМАЦИЯ О ВАКАНСИИ И ТРЕБОВАНИЯХ\n\n"
    
    # Название вакансии
    if hasattr(vacancy, 'name') and vacancy.name:
        formatted_text += f"### Позиция\n{vacancy.name}\n\n"
    
    # Компания
    if hasattr(vacancy, 'employer') and vacancy.employer:
        employer_name = vacancy.employer
        if hasattr(employer_name, 'name'):
            employer_name = employer_name.name
        formatted_text += f"### Компания\n{employer_name}\n\n"
    
    # Полное описание вакансии
    if hasattr(vacancy, 'description') and vacancy.description:
        formatted_text += "### Описание вакансии и требования к кандидату\n"
        # Убираем HTML теги для чистоты
        clean_description = re.sub(r'<[^>]+>', '', str(vacancy.description))
        formatted_text += f"{clean_description}\n\n"
    
    # Ключевые навыки
    if hasattr(vacancy, 'key_skills') and vacancy.key_skills:
        formatted_text += "### Ключевые требуемые навыки\n"
        skill_list = vacancy.key_skills if isinstance(vacancy.key_skills, list) else [vacancy.key_skills]
        for skill in skill_list:
            skill_name = skill
            if hasattr(skill, 'name'):
                skill_name = skill.name
            formatted_text += f"- {skill_name}\n"
        formatted_text += "\n"
    
    # Требуемый опыт работы
    if hasattr(vacancy, 'experience') and vacancy.experience:
        experience_name = vacancy.experience
        if hasattr(experience_name, 'name'):
            experience_name = experience_name.name
        formatted_text += f"### Требуемый опыт работы\n{experience_name}\n\n"
    
    # Условия работы
    if hasattr(vacancy, 'employment') and vacancy.employment:
        employment_name = vacancy.employment
        if hasattr(employment_name, 'name'):
            employment_name = employment_name.name
        formatted_text += f"### Тип занятости\n{employment_name}\n\n"
    
    if hasattr(vacancy, 'schedule') and vacancy.schedule:
        schedule_name = vacancy.schedule
        if hasattr(schedule_name, 'name'):
            schedule_name = schedule_name.name
        formatted_text += f"### График работы\n{schedule_name}\n\n"
    
    # Зарплата
    if hasattr(vacancy, 'salary') and vacancy.salary:
        formatted_text += f"### Зарплата\n{vacancy.salary}\n\n"
    
    logger.debug(f"Вакансия отформатирована, длина текста: {len(formatted_text)} символов")
    return formatted_text


def format_dialog_history(dialog_messages: List[DialogMessage]) -> str:
    """Форматирует историю диалога для передачи в LLM промпты.
    
    Args:
        dialog_messages: Список сообщений диалога
        
    Returns:
        str: Отформатированная история диалога
    """
    if not dialog_messages:
        return "## ИСТОРИЯ ДИАЛОГА\n\nДиалог только начинается.\n\n"
    
    formatted_text = "## ИСТОРИЯ ПРЕДЫДУЩЕГО ДИАЛОГА\n\n"
    
    for msg in dialog_messages:
        speaker_name = "HR-менеджер" if msg.speaker == "HR" else "Кандидат"
        question_type_info = ""
        if msg.speaker == "HR" and msg.question_type:
            question_type_info = f" ({msg.question_type.value})"
        
        formatted_text += f"**{speaker_name} (раунд {msg.round_number}{question_type_info}):**\n{msg.message}\n\n"
    
    logger.debug(f"История диалога отформатирована: {len(dialog_messages)} сообщений")
    return formatted_text


def create_candidate_profile_and_config(resume: ResumeInfo, 
                                       vacancy: VacancyInfo) -> Tuple[CandidateProfile, InterviewConfiguration]:
    """Создает профиль кандидата и конфигурацию интервью.
    
    Основная функция для анализа входных данных и подготовки 
    параметров для проведения симуляции интервью.
    
    Args:
        resume: Информация о резюме
        vacancy: Информация о вакансии
        
    Returns:
        Tuple[CandidateProfile, InterviewConfiguration]: Профиль и конфигурация
    """
    logger.info("Создаем профиль кандидата и конфигурацию интервью")
    
    # Анализируем профиль кандидата
    analyzer = SmartCandidateAnalyzer()
    profile = analyzer.analyze_candidate_profile(resume)
    
    # Строим конфигурацию интервью
    config_builder = InterviewConfigurationBuilder()
    config = config_builder.build_interview_config(profile, vacancy)
    
    logger.info("Профиль и конфигурация созданы успешно")
    return profile, config