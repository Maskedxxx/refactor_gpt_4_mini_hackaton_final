# examples/show_full_prompt.py
# --- agent_meta ---
# role: llm-cover-letter-prompt-demo
# owner: @backend
# contract: Демонстрация полного промпта для генерации сопроводительного письма
# last_reviewed: 2025-08-14
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
from src.llm_cover_letter.options import CoverLetterOptions
from src.llm_cover_letter.models import RoleType
from src.llm_cover_letter.prompts.builders import DefaultContextBuilder, DefaultPromptBuilder
from src.llm_cover_letter.formatter import format_resume_for_cover_letter, format_vacancy_for_cover_letter


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


def demonstrate_prompt(prompt_version="cover_letter.v2", role_hint=None, extra_context=None):
    """Демонстрация полного промпта."""
    print(f"=== ДЕМОНСТРАЦИЯ ПОЛНОГО ПРОМПТА ({prompt_version}) ===\n")
    
    # Загружаем тестовые данные
    resume, vacancy = load_test_data()
    
    # Настройки генерации
    options = CoverLetterOptions(
        prompt_version=prompt_version,
        role_hint=role_hint,
        language="ru",
        length="MEDIUM",
        extra_context=extra_context
    )
    
    print("📋 ИСХОДНЫЕ ДАННЫЕ:")
    print(f"Резюме: {resume.first_name} {resume.last_name} - {resume.title}")
    print(f"Вакансия: {vacancy.name}")
    print(f"Опции: version={options.prompt_version}, role_hint={options.role_hint}")
    if options.extra_context:
        print(f"Доп. контекст: {options.extra_context}")
    print()
    
    # Построение контекста
    context_builder = DefaultContextBuilder()
    ctx = context_builder.build(resume, vacancy, options)
    
    print("🔧 ПОСТРОЕННЫЙ КОНТЕКСТ:")
    for key, value in ctx.items():
        if key in ["company_tone_instruction", "role_adaptation_instruction"]:
            print(f"{key}: {value[:100]}...")
        else:
            print(f"{key}: {value}")
    print()
    
    # Форматирование блоков
    resume_block = format_resume_for_cover_letter(resume)
    vacancy_block = format_vacancy_for_cover_letter(vacancy)
    
    print("📄 ФОРМАТИРОВАННЫЕ БЛОКИ:")
    print(f"Resume block: {len(resume_block)} символов")
    print(f"Vacancy block: {len(vacancy_block)} символов")
    print()
    
    # Сборка промпта
    prompt_builder = DefaultPromptBuilder()
    prompt = prompt_builder.build(
        resume_block=resume_block,
        vacancy_block=vacancy_block,
        ctx=ctx,
        options=options
    )
    
    print("=" * 80)
    print("🎯 ФИНАЛЬНЫЙ SYSTEM PROMPT:")
    print("=" * 80)
    print(prompt.system)
    print()
    
    print("=" * 80)
    print("🎯 ФИНАЛЬНЫЙ USER PROMPT:")
    print("=" * 80)
    print(prompt.user[:20000] + "..." if len(prompt.user) > 20000 else prompt.user)
    print()
    
    print("📊 СТАТИСТИКА:")
    print(f"System prompt: {len(prompt.system)} символов")
    print(f"User prompt: {len(prompt.user)} символов")
    print(f"Общий размер: {len(prompt.system) + len(prompt.user)} символов")


def main():
    """Демонстрация различных вариантов промптов."""
    
    # 1. Базовая версия v1
    print("1️⃣ БАЗОВАЯ ВЕРСИЯ V1")
    demonstrate_prompt(
        prompt_version="cover_letter.v1", 
        role_hint=RoleType.ML_ENGINEER
    )
    
    print("\n" + "="*100 + "\n")
    
    # 2. Улучшенная версия v2
    print("2️⃣ УЛУЧШЕННАЯ ВЕРСИЯ V2")
    demonstrate_prompt(
        prompt_version="cover_letter.v2", 
        role_hint=RoleType.DATA_SCIENTIST
    )
    
    print("\n" + "="*100 + "\n")
    
    # 3. С дополнительным контекстом
    print("3️⃣ С ДОПОЛНИТЕЛЬНЫМ КОНТЕКСТОМ")
    demonstrate_prompt(
        prompt_version="cover_letter.v2",
        role_hint=RoleType.ML_ENGINEER,
        extra_context={
            "deadline": "срочно, начало в течение недели",
            "remote": "полная удаленка",
            "team_size": "команда 5 человек"
        }
    )
    
    print("\n" + "="*100 + "\n")
    
    # 4. Автоопределение роли
    print("4️⃣ АВТООПРЕДЕЛЕНИЕ РОЛИ (role_hint=None)")
    demonstrate_prompt(
        prompt_version="cover_letter.v2",
        role_hint=None  # будет определено автоматически из resume.title
    )


if __name__ == "__main__":
    main()