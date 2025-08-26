#!/usr/bin/env python3
"""
Скрипт для полной трассировки промпта gap_analyzer
Показывает окончательный промпт который отправляется в LLM
"""

import os
import sys
import json
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent / "src"))

from webapp.storage_docs import SessionStore, ResumeStore, VacancyStore
from llm_gap_analyzer.formatter import format_resume_data, format_vacancy_data
from llm_gap_analyzer.prompts.mappings import extract_requirements_from_vacancy
from llm_gap_analyzer.prompts.templates import get_template
from llm_features.base.options import BaseLLMOptions

def main():
    if len(sys.argv) < 2:
        print("Usage: python trace_full_prompt.py <session_id>")
        print("Example: python trace_full_prompt.py d7b4aab2-8bd4-4fdf-bbad-2b9aa44d31f0")
        return 1
    
    session_id = sys.argv[1]
    db_path = os.getenv("WEBAPP_DB_PATH", "app.sqlite3")
    
    print(f"=== Полная трассировка промпта gap_analyzer для сессии {session_id} ===")
    
    # Инициализируем стораджи
    session_store = SessionStore(db_path)
    resume_store = ResumeStore(db_path)
    vacancy_store = VacancyStore(db_path)
    
    # Получаем данные сессии
    session_data = session_store.get(session_id)
    if not session_data:
        print("❌ Сессия не найдена")
        return 1
    
    resume = resume_store.get(session_data['resume_id'])
    vacancy = vacancy_store.get(session_data['vacancy_id'])
    
    if not resume or not vacancy:
        print("❌ Резюме или вакансия не найдены")
        return 1
    
    print("✅ Данные загружены")
    
    # Формируем блоки точно как в service.py
    resume_block = format_resume_data(resume.model_dump())
    vacancy_block = format_vacancy_data(vacancy.model_dump())
    requirements_block = extract_requirements_from_vacancy(vacancy)
    
    # Включаем проблематичный блок для демонстрации проблемы
    from llm_gap_analyzer.prompts.mappings import build_skills_match_summary
    skills_match_summary_block = build_skills_match_summary(resume, vacancy)
    extra_context_block = "(нет)"
    
    # Получаем шаблон
    template = get_template("gap_analyzer.v1")
    
    # Формируем контекст
    ctx = {
        "language": "Russian",
        "resume_block": resume_block,
        "vacancy_block": vacancy_block,
        "requirements_block": requirements_block,
        "skills_match_summary_block": skills_match_summary_block,
        "extra_context_block": extra_context_block,
    }
    
    # Рендерим итоговый промпт
    prompt = template.render(ctx)
    
    # Сохраняем полную трассировку
    trace_file = f"gap_analyzer_FULL_PROMPT_TRACE_{session_id[:8]}.txt"
    with open(trace_file, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("🔍 GAP ANALYZER - ПОЛНАЯ ТРАССИРОВКА ПРОМПТА (ТЕКУЩАЯ ПРОБЛЕМНАЯ ВЕРСИЯ)\n")
        f.write("="*100 + "\n\n")
        
        f.write("СТАТУС ПРОБЛЕМ:\n")
        f.write("- ❌ ПРОБЛЕМАТИЧНЫЙ блок skills_match_summary ВКЛЮЧЕН (показывает только 1 совпадение!)\n")
        f.write("- ❌ LLM получает ЛОЖНУЮ сводку вместе с детальными данными\n")
        f.write("- ❌ Используется поле 'skills' вместо 'skill_set' в formatter.py\n")
        f.write("- ❌ Функция analyze_skills_match() делает примитивное сравнение строк\n\n")
        
        f.write("SYSTEM MESSAGE:\n")
        f.write("="*80 + "\n")
        f.write(prompt.system + "\n\n")
        
        f.write("USER MESSAGE:\n")
        f.write("="*80 + "\n")
        f.write(prompt.user + "\n\n")
        
        f.write("СТАТИСТИКА КОНТЕКСТА:\n")
        f.write("="*80 + "\n")
        f.write(f"📊 resume_block: {len(resume_block):,} символов\n")
        f.write(f"📊 vacancy_block: {len(vacancy_block):,} символов\n")
        f.write(f"📊 requirements_block: {len(requirements_block):,} символов\n")
        f.write(f"📊 skills_match_summary_block: {len(skills_match_summary_block):,} символов (ПРОБЛЕМАТИЧНЫЙ!)\n")
        f.write(f"📊 ОБЩИЙ ПРОМПТ: {len(prompt.system + prompt.user):,} символов\n\n")
        
        # Анализ навыков
        resume_skills = resume.skill_set or []
        vacancy_skills = vacancy.key_skills or []
        f.write("АНАЛИЗ НАВЫКОВ:\n")
        f.write("="*80 + "\n")
        f.write(f"👤 Навыки в резюме ({len(resume_skills)}): {', '.join(resume_skills[:10])}{'...' if len(resume_skills) > 10 else ''}\n")
        f.write(f"💼 Навыки в вакансии ({len(vacancy_skills)}): {', '.join(vacancy_skills)}\n")
        
        # Поиск потенциальных совпадений
        potential_matches = []
        for v_skill in vacancy_skills:
            for r_skill in resume_skills:
                if (v_skill.lower() in r_skill.lower() or r_skill.lower() in v_skill.lower() or
                    any(word in r_skill.lower() for word in ['ai', 'ml', 'llm']) and 
                    any(word in v_skill.lower() for word in ['ai', 'ml', 'nlp'])):
                    potential_matches.append(f"'{v_skill}' ↔ '{r_skill}'")
        
        f.write(f"🎯 Потенциальные семантические совпадения ({len(potential_matches)}): \n")
        for match in potential_matches[:5]:
            f.write(f"   {match}\n")
    
    print(f"🎯 ПОЛНАЯ ТРАССИРОВКА ПРОМПТА СОХРАНЕНА В: {trace_file}")
    print(f"📏 Размер промпта: {len(prompt.system + prompt.user):,} символов")
    print("🔧 Проблематичный блок skills_match_summary: ВКЛЮЧЕН ❌")
    print(f"⚠️  LLM видит ЛОЖНУЮ сводку: только {skills_match_summary_block.count('Docker')} совпадение из 30+ навыков!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())