# examples/show_full_interview_simulation_prompts.py
# --- agent_meta ---
# role: interview-simulation-prompt-demo
# owner: @backend
# contract: Демонстрация всех промптов симуляции интервью (HR + Candidate) на всех этапах
# last_reviewed: 2025-08-18
# interfaces:
#   - main(): печать всех промптов для каждого раунда интервью
# --- /agent_meta ---

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from src.models import ResumeInfo, VacancyInfo
from src.llm_interview_simulation import (
    LLMInterviewSimulationGenerator,
    InterviewSimulationOptions,
    DialogMessage,
    QuestionType
)
from src.llm_interview_simulation.formatter import (
    format_resume_for_interview_simulation,
    format_vacancy_for_interview_simulation,
    format_dialog_history,
    create_candidate_profile_and_config
)
from src.llm_interview_simulation.prompts import InterviewPromptBuilder
from src.llm_interview_simulation.config import get_question_types_for_round


def load_test_data() -> tuple[ResumeInfo, VacancyInfo]:
    """Загружает тестовые данные резюме и вакансии."""
    data_dir = Path(__file__).parent.parent / "tests" / "data"
    
    # Пытаемся загрузить существующие данные, если нет - создаем простые
    try:
        with (data_dir / "simple_resume.json").open("r", encoding="utf-8") as f:
            resume_data = json.load(f)
    except FileNotFoundError:
        resume_data = create_sample_resume()
    
    try:
        with (data_dir / "simple_vacancy.json").open("r", encoding="utf-8") as f:
            vacancy_data = json.load(f)
    except FileNotFoundError:
        vacancy_data = create_sample_vacancy()
    
    resume = ResumeInfo(**resume_data)
    vacancy = VacancyInfo(**vacancy_data)
    return resume, vacancy


def create_sample_resume() -> Dict[str, Any]:
    """Создает простое тестовое резюме."""
    return {
        "first_name": "Алексей",
        "last_name": "Смирнов",
        "title": "Middle Python Developer",
        "skills": "Опыт разработки на Python 4 года. Django, FastAPI, PostgreSQL, Redis, Docker. Участие в проектах от архитектуры до деплоя.",
        "skill_set": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker", "Git"],
        "experience": [
            {
                "company": "Tech Solutions",
                "position": "Python Developer",
                "start": "2020-06",
                "end": "2024-12",
                "description": "Разработка веб-приложений, API, работа с базами данных, код-ревью"
            }
        ],
        "education": {
            "level": {"name": "Высшее"},
            "primary": [{"name": "СПбГУ", "result": "Бакалавр информатики", "year": "2020"}]
        },
        "total_experience": {"months": 54},
        "salary": {"amount": 180000, "currency": "RUR"}
    }


def create_sample_vacancy() -> Dict[str, Any]:
    """Создает простую тестовую вакансию."""
    return {
        "name": "Senior Python Developer",
        "employer": {"name": "InnovateTech"},
        "description": "Ищем опытного Python разработчика для работы над высоконагруженными системами. Требования: Python, Django/FastAPI, PostgreSQL, Redis, Docker.",
        "key_skills": [
            {"name": "Python"},
            {"name": "Django"},
            {"name": "PostgreSQL"},
            {"name": "Redis"}
        ],
        "experience": {"name": "От 3 до 6 лет"},
        "employment": {"name": "Полная занятость"},
        "schedule": {"name": "Полный день"},
        "salary": "от 200 000 до 300 000 руб."
    }


def create_mock_dialog_history(round_number: int) -> List[DialogMessage]:
    """Создает макет истории диалога для демонстрации."""
    
    mock_dialogs = {
        1: [
            DialogMessage(
                speaker="HR",
                message="Добро пожаловать! Расскажите, пожалуйста, о себе и своём опыте разработки.",
                round_number=1,
                question_type=QuestionType.INTRODUCTION
            ),
            DialogMessage(
                speaker="Candidate",
                message="Привет! Меня зовут Алексей, я Python разработчик с 4-летним опытом. Работаю с Django и FastAPI, есть опыт с PostgreSQL и Docker.",
                round_number=1,
                response_quality=4
            )
        ],
        2: [
            DialogMessage(
                speaker="HR",
                message="Расскажите подробнее о вашем опыте с Django. Какие сложные задачи решали?",
                round_number=2,
                question_type=QuestionType.TECHNICAL_SKILLS
            ),
            DialogMessage(
                speaker="Candidate",
                message="В последнем проекте создавал систему аналитики с Django. Основная сложность была в оптимизации запросов - использовал select_related, prefetch_related, добавил индексы. Производительность выросла в 5 раз.",
                round_number=2,
                response_quality=5
            )
        ],
        3: [
            DialogMessage(
                speaker="HR",
                message="Опишите ситуацию, когда вам пришлось работать в команде над сложной задачей. Как решали конфликты?",
                round_number=3,
                question_type=QuestionType.BEHAVIORAL_STAR
            ),
            DialogMessage(
                speaker="Candidate",
                message="Был проект интеграции с внешним API. Возник конфликт по архитектуре с коллегой. Организовал встречу, выслушал все точки зрения, предложил создать прототипы обоих подходов. В итоге выбрали гибридное решение.",
                round_number=3,
                response_quality=4
            )
        ]
    }
    
    # Возвращаем историю до указанного раунда
    history = []
    for r in range(1, round_number):
        if r in mock_dialogs:
            history.extend(mock_dialogs[r])
    
    return history


async def demonstrate_all_prompts():
    """Демонстрирует все промпты для симуляции интервью."""
    
    print("🎭 " + "=" * 100)
    print("     ДЕМОНСТРАЦИЯ ВСЕХ ПРОМПТОВ СИМУЛЯЦИИ ИНТЕРВЬЮ")
    print("=" * 100)
    
    # 1. Загружаем тестовые данные
    print("\n📖 Загружаем тестовые данные...")
    resume, vacancy = load_test_data()
    
    print(f"   Кандидат: {resume.first_name} {resume.last_name}")
    print(f"   Позиция: {vacancy.name}")
    
    # 2. Создаем профиль кандидата и конфигурацию
    print("\n🔍 Анализируем профиль кандидата...")
    candidate_profile, interview_config = create_candidate_profile_and_config(resume, vacancy)
    
    print(f"   Определенный уровень: {candidate_profile.detected_level.value}")
    print(f"   Определенная роль: {candidate_profile.detected_role.value}")
    print(f"   Количество раундов: {interview_config.target_rounds}")
    print(f"   Сложность: {interview_config.difficulty_level}")
    
    # 3. Форматируем базовые данные
    formatted_resume = format_resume_for_interview_simulation(resume)
    formatted_vacancy = format_vacancy_for_interview_simulation(vacancy)
    
    # 4. Настраиваем опции
    options = InterviewSimulationOptions(
        prompt_version="v1.0",
        target_rounds=interview_config.target_rounds,
        difficulty_level=interview_config.difficulty_level,
        hr_personality="neutral",
        candidate_confidence="medium",
        temperature_hr=0.7,
        temperature_candidate=0.8,
        log_detailed_prompts=True
    )
    
    # 5. Создаем строитель промптов
    prompt_builder = InterviewPromptBuilder()
    
    # 6. Демонстрируем промпты для каждого раунда
    for round_num in range(1, interview_config.target_rounds + 1):
        print(f"\n🎯 " + "=" * 80)
        print(f"                           РАУНД {round_num}")
        print("=" * 80)
        
        # Создаем историю диалога до этого раунда
        dialog_history = create_mock_dialog_history(round_num)
        formatted_history = format_dialog_history(dialog_history)
        
        # Определяем тип вопроса для раунда
        possible_question_types = get_question_types_for_round(round_num)
        question_type = possible_question_types[0] if possible_question_types else QuestionType.FINAL
        
        print(f"\n📋 КОНТЕКСТ РАУНДА {round_num}:")
        print(f"   Тип вопроса: {question_type.value}")
        print(f"   История диалога: {len(dialog_history)} сообщений")
        
        # === HR ПРОМПТ ===
        print(f"\n👤 HR ПРОМПТ (раунд {round_num}):")
        print("-" * 60)
        
        hr_prompt = prompt_builder.build_hr_prompt(
            formatted_resume=formatted_resume,
            formatted_vacancy=formatted_vacancy,
            formatted_history=formatted_history,
            round_number=round_num,
            question_type=question_type,
            candidate_profile=candidate_profile,
            interview_config=interview_config,
            options=options
        )
        
        print(f"\n🔸 SYSTEM PROMPT (HR раунд {round_num}):")
        print("─" * 40)
        print(hr_prompt.system)
        
        print(f"\n🔸 USER PROMPT (HR раунд {round_num}):")
        print("─" * 40)
        print(hr_prompt.user)
        
        # Если это не первый раунд, покажем и candidate промпт
        if round_num > 1:
            # Создаем пример вопроса HR для демонстрации
            sample_hr_questions = {
                2: "Расскажите подробнее о вашем опыте с Django. Какие сложные задачи решали?",
                3: "Опишите ситуацию, когда вам пришлось работать в команде над сложной задачей.",
                4: "Что мотивирует вас в работе разработчика? Почему выбрали нашу компанию?",
                5: "Спасибо за интервью! Есть ли у вас вопросы ко мне?"
            }
            
            sample_question = sample_hr_questions.get(
                round_num, 
                "Расскажите о своем опыте работы с технологиями из нашего стека."
            )
            
            print(f"\n🤵 CANDIDATE ПРОМПТ (раунд {round_num}):")
            print("-" * 60)
            
            candidate_prompt = prompt_builder.build_candidate_prompt(
                formatted_resume=formatted_resume,
                formatted_vacancy=formatted_vacancy,
                formatted_history=formatted_history,
                hr_question=sample_question,
                candidate_profile=candidate_profile,
                options=options
            )
            
            print(f"\n🔸 SYSTEM PROMPT (Candidate раунд {round_num}):")
            print("─" * 40)
            print(candidate_prompt.system)
            
            print(f"\n🔸 USER PROMPT (Candidate раунд {round_num}):")
            print("─" * 40)
            print(candidate_prompt.user)
            
            print(f"\n💬 ПРИМЕР ВОПРОСА HR: {sample_question}")
    
    # 7. Показываем статистику
    print(f"\n📊 " + "=" * 80)
    print("                        СТАТИСТИКА ПРОМПТОВ")
    print("=" * 80)
    
    total_hr_prompts = interview_config.target_rounds
    total_candidate_prompts = interview_config.target_rounds - 1  # Кандидат не отвечает на последний вопрос в демо
    
    print(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего раундов: {interview_config.target_rounds}")
    print(f"   HR промптов: {total_hr_prompts}")
    print(f"   Candidate промптов: {total_candidate_prompts}")
    print(f"   Общее количество промптов: {total_hr_prompts + total_candidate_prompts}")
    
    # Подсчитываем примерные размеры
    sample_hr_length = len(hr_prompt.system) + len(hr_prompt.user)
    sample_candidate_length = len(candidate_prompt.system) + len(candidate_prompt.user) if 'candidate_prompt' in locals() else 0
    
    estimated_total_tokens = ((sample_hr_length * total_hr_prompts) + 
                            (sample_candidate_length * total_candidate_prompts)) // 4  # Примерно 4 символа = 1 токен
    
    print(f"\n💰 ПРИМЕРНАЯ СТОИМОСТЬ (при использовании OpenAI):")
    print(f"   Средний размер HR промпта: ~{sample_hr_length:,} символов")
    if sample_candidate_length > 0:
        print(f"   Средний размер Candidate промпта: ~{sample_candidate_length:,} символов")
    print(f"   Примерное количество токенов: ~{estimated_total_tokens:,}")
    print(f"   Примерная стоимость (gpt-4o-mini): ~${estimated_total_tokens * 0.00015 / 1000:.3f}")
    
    print(f"\n🎯 ТИПЫ ВОПРОСОВ В ИНТЕРВЬЮ:")
    for round_num in range(1, interview_config.target_rounds + 1):
        question_types = get_question_types_for_round(round_num)
        types_str = ", ".join([qt.value for qt in question_types])
        print(f"   Раунд {round_num}: {types_str}")
    
    print(f"\n✅ Демонстрация промптов завершена!")
    print("=" * 100)


async def show_formatted_data_demo():
    """Демонстрирует форматированные данные резюме и вакансии."""
    
    print("\n📄 " + "=" * 80)
    print("           ДЕМОНСТРАЦИЯ ФОРМАТИРОВАННЫХ ДАННЫХ")
    print("=" * 80)
    
    resume, vacancy = load_test_data()
    
    print("\n📋 ФОРМАТИРОВАННОЕ РЕЗЮМЕ:")
    print("-" * 50)
    formatted_resume = format_resume_for_interview_simulation(resume)
    print(formatted_resume)
    
    print("\n💼 ФОРМАТИРОВАННАЯ ВАКАНСИЯ:")
    print("-" * 50)
    formatted_vacancy = format_vacancy_for_interview_simulation(vacancy)
    print(formatted_vacancy)


def main():
    """Основная функция демонстрации."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Демонстрация промптов симуляции интервью")
    parser.add_argument(
        "--show-data", 
        action="store_true", 
        help="Показать только форматированные данные резюме и вакансии"
    )
    parser.add_argument(
        "--round", 
        type=int, 
        help="Показать промпты только для определенного раунда"
    )
    
    args = parser.parse_args()
    
    if args.show_data:
        asyncio.run(show_formatted_data_demo())
    else:
        asyncio.run(demonstrate_all_prompts())


if __name__ == "__main__":
    main()