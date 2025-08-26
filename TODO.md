# TODO - Исправления для проекта

## Проблемы с gap_analyzer

### 1. Неправильное использование поля skills вместо skill_set
**Файл**: `src/llm_gap_analyzer/formatter.py:58`  
**Проблема**: Используется поле `skills` (строка "Знание языков Русский — Родной") вместо `skill_set` (массив технических навыков)  
**Приоритет**: Средний (исправить после решения основной проблемы)  

**Исправление**:
```python
# ❌ НЕПРАВИЛЬНО (текущий код):
formatted_text += f"{resume_data.get('skills', 'Не указаны')}\n\n"

# ✅ ПРАВИЛЬНО:
formatted_text += "## Профессиональные навыки\n"
skill_set = resume_data.get('skill_set', [])
if skill_set:
    formatted_text += "### Технические навыки\n"
    for skill in skill_set:
        formatted_text += f"- {skill}\n"
    formatted_text += "\n"

skills_description = resume_data.get('skills', '')
if skills_description and skills_description != 'Знание языков Русский — Родной':
    formatted_text += "### Дополнительное описание\n"
    formatted_text += f"{skills_description}\n\n"
```

### 2. Функция analyze_skills_match() вводит LLM в заблуждение
**Файл**: `src/llm_cover_letter/formatter.py`, функция `analyze_skills_match()`  
**Проблема**: Примитивное сравнение строк не распознает семантически связанные навыки  
**Приоритет**: КРИТИЧЕСКИЙ - система показывает 1 совпадение вместо 8+ реальных  
**Временное решение**: Отключен проблематичный блок в `src/llm_gap_analyzer/service.py`

**Примеры проблем**:
- "LLM" (в резюме) ≠ "AI" (в вакансии)  
- "Hugging Face" ≠ "ML"  
- "RAG Systems" ≠ "NLP"

**Требуемое исправление**:
```python
def analyze_skills_match_enhanced(resume: ResumeInfo, vacancy: VacancyInfo) -> str:
    # Словарь синонимов и связанных технологий
    skill_synonyms = {
        'ai': ['artificial intelligence', 'llm', 'gpt', 'machine learning', 'deep learning'],
        'ml': ['machine learning', 'ai', 'llm', 'deep learning', 'pytorch', 'tensorflow'], 
        'nlp': ['natural language processing', 'llm', 'text processing', 'hugging face'],
        'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy'],
        'devops': ['docker', 'kubernetes', 'ci/cd', 'jenkins', 'gitlab'],
        # ... расширить список
    }
    
    # Семантическое сопоставление вместо точного совпадения строк
    def find_semantic_matches(resume_skills, vacancy_skills):
        matches = []
        for v_skill in vacancy_skills:
            for r_skill in resume_skills:
                if semantic_match(v_skill, r_skill, skill_synonyms):
                    matches.append((v_skill, r_skill))
        return matches
```

**Альтернативы**:
1. Использовать embedding'и для семантического поиска
2. Интеграция с внешними API (например, skills taxonomy)
3. ML-модель для классификации навыков

### 3. Промпт gap_analyzer нуждается в доработке на основе старой версии
**Приоритет**: ВЫСОКИЙ  
**Проблема**: Текущий промпт менее стабильный чем в предыдущей версии приложения  
**Требуемое исправление**: Проанализировать и адаптировать промпт из старой версии приложения, который показывал более стабильные результаты