# examples/show_full_interview_checklist_prompt.py
# --- agent_meta ---
# role: llm-interview-checklist-prompt-demo
# owner: @backend
# contract: Демонстрация полного промпта для генерации профессионального чек-листа подготовки к интервью
# last_reviewed: 2025-08-18
# interfaces:
#   - main(): демонстрация промпта с тестовыми данными
# --- /agent_meta ---

import json
import sys
from pathlib import Path

# Добавляем путь к корню проекта для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.resume_models import ResumeInfo
from src.models.vacancy_models import VacancyInfo
from src.llm_interview_checklist.options import InterviewChecklistOptions
from src.llm_interview_checklist.models import CandidateLevel, CompanyFormat
from src.llm_interview_checklist.formatter import format_resume_for_interview_prep, format_vacancy_for_interview_prep
from src.llm_interview_checklist.prompts.templates import create_professional_interview_checklist_prompt
from src.llm_interview_checklist.prompts.mappings import (
    detect_vacancy_type_from_description,
    analyze_candidate_level,
    detect_company_format,
    get_candidate_level_guidance,
    get_vacancy_type_adaptation,
    get_company_format_adaptation,
)


def load_test_data():
    """Загрузить тестовые данные из JSON файлов."""
    data_dir = Path(__file__).parent.parent / "tests" / "data"
    
    # Загрузка резюме (упрощенная версия)
    with open(data_dir / "simple_resume.json", "r", encoding="utf-8") as f:
        resume_data = json.load(f)
    resume = ResumeInfo(**resume_data)
    
    # Загрузка вакансии (упрощенная версия)
    with open(data_dir / "simple_vacancy.json", "r", encoding="utf-8") as f:
        vacancy_data = json.load(f)
    vacancy = VacancyInfo(**vacancy_data)
    
    return resume, vacancy


def demonstrate_prompt(
    prompt_version="v1", 
    candidate_level_hint=None, 
    company_format_hint=None,
    preparation_time_available=None,
    focus_areas=None,
    extra_context=None
):
    """Демонстрация полного промпта для профессионального чек-листа подготовки к интервью."""
    print(f"=== ДЕМОНСТРАЦИЯ ПОЛНОГО ПРОМПТА INTERVIEW CHECKLIST ({prompt_version}) ===\n")
    
    # Загружаем тестовые данные
    resume, vacancy = load_test_data()
    
    # Настройки генерации
    options = InterviewChecklistOptions(
        prompt_version=prompt_version,
        candidate_level_hint=candidate_level_hint,
        company_format_hint=company_format_hint,
        preparation_time_available=preparation_time_available,
        focus_areas=focus_areas,
        extra_context=extra_context
    )
    
    print("📋 ИСХОДНЫЕ ДАННЫЕ:")
    print(f"Резюме: {resume.first_name} {resume.last_name} - {resume.title}")
    print(f"Вакансия: {vacancy.name}")
    print(f"Опции: version={options.prompt_version}")
    if options.candidate_level_hint:
        print(f"Уровень кандидата (подсказка): {options.candidate_level_hint}")
    if options.company_format_hint:
        print(f"Формат компании (подсказка): {options.company_format_hint}")
    if options.preparation_time_available:
        print(f"Доступное время подготовки: {options.preparation_time_available}")
    if options.focus_areas:
        print(f"Области фокуса: {options.focus_areas}")
    if options.extra_context:
        print(f"Доп. контекст: {options.extra_context}")
    print()
    
    # Конвертируем модели в словари для форматтеров
    resume_dict = resume.model_dump()
    vacancy_dict = vacancy.model_dump()
    
    # Форматирование блоков
    formatted_resume = format_resume_for_interview_prep(resume_dict)
    formatted_vacancy = format_vacancy_for_interview_prep(vacancy_dict)
    
    print("📄 ФОРМАТИРОВАННЫЕ БЛОКИ:")
    print(f"Resume block: {len(formatted_resume)} символов")
    print(f"Vacancy block: {len(formatted_vacancy)} символов")
    print()
    
    # Анализ контекста
    print("🔍 АНАЛИЗ КОНТЕКСТА:")
    
    # Определение уровня кандидата
    if options.candidate_level_hint:
        try:
            candidate_level = CandidateLevel(options.candidate_level_hint.upper())
        except ValueError:
            candidate_level = analyze_candidate_level(
                resume_dict.get('experience', []), 
                resume_dict.get('total_experience', 0)
            )
    else:
        candidate_level = analyze_candidate_level(
            resume_dict.get('experience', []), 
            resume_dict.get('total_experience', 0)
        )
    
    # Определение типа вакансии
    vacancy_type = detect_vacancy_type_from_description(
        vacancy_dict.get('name', ''), 
        vacancy_dict.get('description', '')
    )
    
    # Определение формата компании
    if options.company_format_hint:
        try:
            company_format = CompanyFormat(options.company_format_hint.upper())
        except ValueError:
            company_format = detect_company_format(
                vacancy_dict.get('company_name', ''), 
                vacancy_dict.get('description', '')
            )
    else:
        company_format = detect_company_format(
            vacancy_dict.get('company_name', ''), 
            vacancy_dict.get('description', '')
        )
    
    print(f"  Уровень кандидата: {candidate_level}")
    print(f"  Тип вакансии: {vacancy_type}")
    print(f"  Формат компании: {company_format}")
    print()
    
    # Получение адаптаций
    level_guidance = get_candidate_level_guidance(candidate_level)
    vacancy_adaptation = get_vacancy_type_adaptation(vacancy_type)
    company_adaptation = get_company_format_adaptation(company_format)
    
    print("🎯 АДАПТАЦИИ ПО КОНТЕКСТУ:")
    print(f"Уровень - фокус: {level_guidance['focus']}")
    print(f"Вакансия - ключевые области: {vacancy_adaptation['key_areas']}")
    print(f"Компания - культурный фокус: {company_adaptation['culture_focus']}")
    print()
    
    # Создание промпта
    prompt_template = create_professional_interview_checklist_prompt(
        formatted_resume=formatted_resume,
        formatted_vacancy=formatted_vacancy,
        candidate_level=candidate_level,
        vacancy_type=vacancy_type,
        company_format=company_format,
        extra_context=options.extra_context,
    )
    
    # Рендеринг промпта
    prompt = prompt_template.render({})
    
    print("=" * 80)
    print("🎯 ФИНАЛЬНЫЙ SYSTEM PROMPT:")
    print("=" * 80)
    print(prompt.system)
    print()
    
    print("=" * 80)
    print("🎯 ФИНАЛЬНЫЙ USER PROMPT:")
    print("=" * 80)
    # Ограничиваем вывод для читаемости
    user_prompt = prompt.user
    if len(user_prompt) > 15000:
        print(user_prompt[:15000] + "\n... (обрезано для читаемости)")
    else:
        print(user_prompt)
    print()
    
    print("📊 СТАТИСТИКА:")
    print(f"System prompt: {len(prompt.system)} символов")
    print(f"User prompt: {len(prompt.user)} символов")
    print(f"Общий размер: {len(prompt.system) + len(prompt.user)} символов")


def main():
    """Демонстрация различных вариантов промптов для чек-листа подготовки к интервью."""
    
    # 1. Базовая версия без подсказок
    print("1️⃣ БАЗОВАЯ ВЕРСИЯ БЕЗ ПОДСКАЗОК (автоопределение)")
    demonstrate_prompt()
    
    print("\n" + "="*100 + "\n")
    
    # 2. С подсказкой уровня кандидата
    print("2️⃣ С ПОДСКАЗКОЙ УРОВНЯ КАНДИДАТА (SENIOR)")
    demonstrate_prompt(
        candidate_level_hint="SENIOR"
    )
    
    print("\n" + "="*100 + "\n")
    
    # 3. С подсказкой формата компании
    print("3️⃣ С ПОДСКАЗКОЙ ФОРМАТА КОМПАНИИ (STARTUP)")
    demonstrate_prompt(
        company_format_hint="STARTUP",
        preparation_time_available="1 неделя"
    )
    
    print("\n" + "="*100 + "\n")
    
    # 4. Полная конфигурация с фокусными областями
    print("4️⃣ ПОЛНАЯ КОНФИГУРАЦИЯ С ФОКУСНЫМИ ОБЛАСТЯМИ")
    demonstrate_prompt(
        candidate_level_hint="MIDDLE",
        company_format_hint="LARGE_CORP",
        preparation_time_available="2 недели",
        focus_areas=["системный дизайн", "алгоритмы", "поведенческие вопросы"],
        extra_context={
            "interview_format": "онлайн",
            "team_info": "команда backend разработки из 8 человек",
            "project_type": "high-load система платежей"
        }
    )
    
    print("\n" + "="*100 + "\n")
    
    # 5. Junior с международной компанией
    print("5️⃣ JUNIOR В МЕЖДУНАРОДНОЙ КОМПАНИИ")
    demonstrate_prompt(
        candidate_level_hint="JUNIOR",
        company_format_hint="INTERNATIONAL",
        preparation_time_available="3 дня",
        focus_areas=["английский язык", "базовые алгоритмы"],
        extra_context={
            "language": "интервью на английском",
            "timezone": "UTC+3",
            "remote": "полностью удаленная работа"
        }
    )


if __name__ == "__main__":
    main()