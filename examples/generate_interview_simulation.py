# examples/generate_interview_simulation.py
# --- agent_meta ---
# role: interview-simulation-cli
# owner: @backend
# contract: CLI: генерация симуляции интервью из ResumeInfo и VacancyInfo (онлайн/офлайн)
# last_reviewed: 2025-08-18
# interfaces:
#   - main(resume_json: Path, vacancy_json: Path, fake_llm: bool) -> int
# --- /agent_meta ---

from __future__ import annotations

import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any
import time
from datetime import datetime

from src.utils import get_logger
from src.parsing.llm.client import LLMClient
from pydantic import BaseModel
from src.parsing.resume.parser import LLMResumeParser
from src.parsing.vacancy.mapper import map_hh_json_to_vacancy
from src.models import ResumeInfo, VacancyInfo
# ВАЖНО: импорты модулей симуляции выполняются внутри main() после установки переменной окружения
# INTERVIEW_SIM_CONFIG (если передан путь к YAML), чтобы конфиг подхватился до инициализации модулей.

log = get_logger("examples.generate_interview_simulation")


def _read_json(path: Path) -> dict[str, Any]:
    """Читает JSON файл и возвращает данные."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TracingLLMClient(LLMClient):
    """LLM клиент с полным трейсингом всех промптов и ответов."""
    
    def __init__(self, base_llm: LLMClient, trace_file: Path):
        """Инициализация с базовым LLM и файлом трейсинга."""
        self.base_llm = base_llm
        self.trace_file = trace_file
        self.traces = []
        self.call_count = 0
    
    async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):
        """Генерирует ответ с трейсингом."""
        self.call_count += 1
        
        # Сохраняем промпт
        prompt_text = self._extract_prompt_text(prompt)
        
        trace_entry = {
            "call_id": self.call_count,
            "timestamp": time.time(),
            "model_name": model_name or "default",
            "temperature": temperature,
            "max_tokens": max_tokens,
            "prompt": prompt_text,
            "schema": str(schema),
            "response": None,
            "error": None
        }
        
        try:
            # Генерируем ответ
            response = await self.base_llm.generate_structured(
                prompt, schema, 
                model_name=model_name, 
                temperature=temperature, 
                max_tokens=max_tokens
            )
            trace_entry["response"] = str(response)
            
        except Exception as e:
            trace_entry["error"] = str(e)
            raise
        finally:
            # Сохраняем трейс
            self.traces.append(trace_entry)
            self._save_trace()
        
        return response
    
    def _extract_prompt_text(self, prompt) -> str:
        """Извлекает текст промпта для сохранения."""
        if hasattr(prompt, 'system') and hasattr(prompt, 'user'):
            return f"SYSTEM: {prompt.system}\n\nUSER: {prompt.user}"
        elif hasattr(prompt, 'content'):
            return prompt.content
        else:
            return str(prompt)
    
    def _save_trace(self):
        """Сохраняет все трейсы в файл."""
        trace_data = {
            "session_info": {
                "total_calls": len(self.traces),
                "created_at": time.time(),
                "trace_file": str(self.trace_file)
            },
            "traces": self.traces
        }
        
        with self.trace_file.open("w", encoding="utf-8") as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)


class _FakeLLMForInterview(LLMClient):
    """Fake LLM клиент для демонстрации без реальных API вызовов."""
    
    def __init__(self):
        """Инициализация с счетчиком вызовов."""
        self.call_count = 0
        self.hr_questions = [
            "Добро пожаловать! Расскажите, пожалуйста, о себе и своём опыте разработки на Python.",
            "Отлично! Расскажите более подробно о вашем проекте на Django - какие сложности вы решали?",
            "Интересно! Опишите ситуацию, когда вам пришлось работать в команде над сложной задачей. Как вы организовали процесс?",
            "Хорошо! Что мотивирует вас в работе разработчика? Почему выбрали именно нашу компанию?",
            "Спасибо за подробные ответы! Есть ли у вас вопросы ко мне о компании или проектах?"
        ]
        self.candidate_answers = [
            "Привет! Меня зовут Иван, я Python разработчик с 3-летним опытом. Начинал как Junior в небольшой студии, сейчас работаю Middle разработчиком в ТехСофт. Специализируюсь на веб-разработке с Django и FastAPI, есть опыт с PostgreSQL и Docker.",
            "В последнем проекте создавал систему управления заказами для e-commerce. Основная сложность была в оптимизации запросов к базе - изначально страница загружалась 5 секунд. Добавил индексы, переписал некоторые запросы через select_related, использовал кеширование Redis. В итоге снизил время загрузки до 0.8 секунд.",
            "Недавно мы делали интеграцию с внешним API платежной системы. Я был ответственным за архитектуру. Разбил команду: один делал модели данных, другой - API клиент, я координировал и делал основную логику. Использовали code review, daily standups. Проект завершили в срок без критических багов.",
            "Мне нравится решать сложные технические задачи и видеть как мой код помогает пользователям. В вашей компании привлекает работа с современными технологиями и возможность развиваться в микросервисной архитектуре. Изучал ваши проекты на GitHub - очень качественный код!",
            "Да! Какие основные технологические вызовы сейчас стоят перед командой? И как организован процесс code review?"
        ]
    
    async def generate_structured(self, prompt, schema, *, model_name=None, temperature=0.0, max_tokens=None):
        """Генерирует фейковые ответы для симуляции."""
        # Имитируем задержку API
        await asyncio.sleep(0.5)
        
        self.call_count += 1
        
        # Если это строка (HR или Candidate ответ)
        if schema == str:
            prompt_text = prompt.system.lower() if hasattr(prompt, 'system') else str(prompt).lower()
            
            # Определяем тип промпта
            if "hr-менеджер" in prompt_text or "опытный hr" in prompt_text:
                # HR вопрос
                question_index = min(len(self.hr_questions) - 1, (self.call_count - 1) // 2)
                return self.hr_questions[question_index]
            else:
                # Candidate ответ
                answer_index = min(len(self.candidate_answers) - 1, (self.call_count - 2) // 2)
                return self.candidate_answers[answer_index]
        
        # Если ожидается Pydantic-модель с текстом, собираем её
        try:
            if isinstance(schema, type) and issubclass(schema, BaseModel):
                prompt_text = prompt.system.lower() if hasattr(prompt, 'system') else str(prompt).lower()
                if "hr-менеджер" in prompt_text or "опытный hr" in prompt_text:
                    idx = min(len(self.hr_questions) - 1, (self.call_count - 1) // 2)
                    return schema.model_validate({"text": self.hr_questions[idx]})
                else:
                    idx = min(len(self.candidate_answers) - 1, (self.call_count - 2) // 2)
                    return schema.model_validate({"text": self.candidate_answers[idx]})
        except Exception:
            pass
        # Fallback
        return "Fake response"


async def _load_resume(resume_pdf: Path | None, fake_llm: bool) -> ResumeInfo:
    """Загружает резюме из PDF или создает fake данные."""
    if fake_llm or resume_pdf is None:
        # Возвращаем fake резюме напрямую
        return ResumeInfo.model_validate({
            "first_name": "Максим",
            "last_name": "Немов",
            "title": "NLP LLM Engineer",
            "total_experience": 48,
            "skills": "AI Engineer с 3+ годами создания production LLM-решений и RAG-систем. Автоматизировал бизнес-процессы с impact $50K+ экономии, повысил конверсию продаж на 35% и точность корпоративного поиска на 40%. Специализируюсь на conversational AI, voice технологиях и образовательных AI-платформах.",
            "skill_set": ["Python", "LLM", "LangChain", "Docker", "SQL", "Git", "vLLM", "RAG Systems", "Fine-tuning", "Prompt Engineering"],
            "experience": [
                {
                    "company": "Союзснаб",
                    "position": "AI engineer",
                    "start": "2024-05",
                    "end": None,
                    "description": "Автоматизировал HR-процессы, сократив время создания поздравлений с 3+ часов до 30 секунд. Повысил точность корпоративного поиска на 40% через внедрение LLM-ансамбля. Создал многоуровневый ансамбль локальных LLM (Llama 3: 7B + 70B модели)."
                },
                {
                    "company": "Академия астрологии Ирины Чайки",
                    "position": "AI Engineer",
                    "start": "2023-05",
                    "end": "2024-05",
                    "description": "Увеличил конверсию продаж на 35% через персонализированный AI-консультант. Автоматизировал 65% работы кураторов, сэкономив $50K+ годовых расходов. Разработал персонализированного чат-бота на базе GPT-4."
                }
            ],
            "education": {
                "level": {"name": "Высшее"},
                "primary": [{
                    "name": "МГУ им. Ломоносова",
                    "result": "Магистр информатики",
                    "year": 2020
                }]
            },
            "languages": [
                {"name": "Русский", "level": {"name": "Родной"}},
                {"name": "Английский", "level": {"name": "B2 — Выше среднего"}}
            ],
            "contact": [{"type": {"name": "Эл. почта"}, "value": "maksim.nemov@example.com"}],
            "site": [{"type": {"name": "GitHub"}, "url": "https://github.com/mnemov"}],
            "employments": ["Полная занятость"],
            "schedules": ["Полный день"],
            "professional_roles": [{"name": "AI Engineer"}],
            "salary": {"amount": 200000}
        })
    else:
        # Реальный парсинг PDF
        parser = LLMResumeParser()
        return await parser.parse(resume_pdf)


async def main(resume_source: Path | None, vacancy_json: Path, fake_llm: bool = False, trace: bool = False, save_result: bool = False) -> int:
    """Основная функция для генерации симуляции интервью.
    
    Args:
        resume_json: Путь к JSON файлу с резюме
        vacancy_json: Путь к JSON файлу с вакансией  
        fake_llm: Использовать fake LLM вместо реального OpenAI
        
    Returns:
        int: Код возврата (0 = успех)
    """
    log.info("🎭 Запуск генерации симуляции интервью")
    
    try:
        # 1. Загружаем данные
        log.info("📖 Загружаем данные резюме и вакансии")
        
        # Определяем тип резюме (PDF или fake)
        if resume_source and resume_source.suffix.lower() == '.pdf':
            log.info(f"📄 Парсим PDF резюме: {resume_source}")
            resume = await _load_resume(resume_source, fake_llm)
        else:
            log.info("🎭 Используем fake резюме для демонстрации")
            resume = await _load_resume(None, True)
        
        # Загружаем вакансию
        vacancy_data = _read_json(vacancy_json)
        if 'id' in vacancy_data:  # HH.ru формат
            vacancy = map_hh_json_to_vacancy(vacancy_data)
        else:
            vacancy = VacancyInfo.model_validate(vacancy_data)
        
        log.info(f"   Кандидат: {resume.first_name} {resume.last_name}")
        log.info(f"   Позиция: {vacancy.name}")
        
        # 2. Настраиваем генератор с трейсингом
        generator_kwargs = {}
        trace_file = None
        
        if trace:
            # Создаем файл для трейсинга
            trace_dir = Path("output/traces")
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_file = trace_dir / f"interview_trace_{uuid.uuid4().hex[:8]}.json"
            log.info(f"📊 Включен полный трейсинг: {trace_file}")
        
        if fake_llm:
            log.info("🔧 Используем fake LLM для демонстрации")
            base_llm = _FakeLLMForInterview()
        else:
            log.info("🔧 Используем реальный OpenAI API")
            if not os.getenv("OPENAI_API_KEY"):
                log.error("❌ OPENAI_API_KEY не установлен! Используйте --fake-llm для демо")
                return 1
            # Конструируем OpenAI SDK клиент и передаем дефолтную модель в адаптер
            from openai import OpenAI
            from src.parsing.llm.client import OpenAILLMClient
            # Модель берем из переменной окружения или из YAML/дефолтов модуля
            try:
                from src.llm_interview_simulation.config import default_settings as _sim_defaults
                default_model = os.getenv("OPENAI_MODEL_NAME", _sim_defaults.openai_model_name)
            except Exception:
                default_model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini-2024-07-18")
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            base_llm = OpenAILLMClient(client, default_model)
        
        # Оборачиваем в трейсинг если нужно
        if trace and trace_file:
            generator_kwargs["llm"] = TracingLLMClient(base_llm, trace_file)
        else:
            generator_kwargs["llm"] = base_llm
        
        # Импорты после возможной установки INTERVIEW_SIM_CONFIG
        from src.llm_interview_simulation import (
            LLMInterviewSimulationGenerator,
            InterviewSimulationOptions,
        )

        generator = LLMInterviewSimulationGenerator(**generator_kwargs)
        
        # 3. Настраиваем опции
        options = InterviewSimulationOptions(
            prompt_version="v1.0",
            target_rounds=5,
            difficulty_level="medium",
            include_behavioral=True,
            include_technical=True,
            hr_personality="neutral",
            candidate_confidence="medium",
            temperature_hr=0.7,
            temperature_candidate=0.8,
            log_detailed_prompts=True  # Включаем детальное логирование промптов
        )
        
        log.info(f"🎯 Конфигурация: {options.target_rounds} раундов, сложность {options.difficulty_level}")
        
        # 4. Генерируем симуляцию интервью
        log.info("🚀 Начинаем симуляцию интервью...")
        start_time = time.time()
        
        result = await generator.generate(resume, vacancy, options)
        
        elapsed_time = time.time() - start_time
        log.info(f"✅ Симуляция завершена за {elapsed_time:.1f} секунд")
        
        # 5. Выводим результаты
        print("\n" + "=" * 80)
        print("🎭 РЕЗУЛЬТАТЫ СИМУЛЯЦИИ ИНТЕРВЬЮ")
        print("=" * 80)
        
        print("\n📋 БАЗОВАЯ ИНФОРМАЦИЯ:")
        print(f"   Позиция: {result.position_title}")
        print(f"   Кандидат: {result.candidate_name}")
        print(f"   Уровень: {result.candidate_profile.detected_level.value}")
        print(f"   Роль: {result.candidate_profile.detected_role.value}")
        print(f"   Опыт: {result.candidate_profile.years_of_experience} лет")
        
        print("\n🎯 СТАТИСТИКА ИНТЕРВЬЮ:")
        print(f"   Раундов проведено: {result.total_rounds_completed}")
        print(f"   Типы вопросов: {', '.join([qt.value for qt in result.covered_question_types])}")
        
        print("\n💬 ДИАЛОГ ИНТЕРВЬЮ:")
        for i, msg in enumerate(result.dialog_messages, 1):
            speaker_icon = "👤 HR" if msg.speaker == "HR" else "🤵 Кандидат"
            quality_info = ""
            question_type_info = f" [{msg.question_type.value}]" if msg.question_type else ""
            
            print(f"\n   {i}. {speaker_icon} (раунд {msg.round_number}){question_type_info}{quality_info}:")
            print(f"      {msg.message}")
        
        # Блок оценки удален в этой версии
        
        # 6. Сохраняем результат для PDF экспорта (если запрошено)
        if save_result:
            tests_data_dir = Path("tests/data")
            tests_data_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_result_file = tests_data_dir / f"interview_simulation_result_{timestamp}.json"
            
            # Конвертируем в JSON-сериализуемый формат
            result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.dict()
            
            with test_result_file.open("w", encoding="utf-8") as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2)
            
            print("\n💾 Результат сохранен для PDF экспорта:")
            print(f"   📁 {test_result_file}")
            print(f"   📦 Для PDF генерации: python examples/test_pdf_export.py --feature interview_simulation --result-file {test_result_file.name}")
            print("=" * 80)
            return 0
        
        # Обычное сохранение в output/
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        session_id = uuid.uuid4().hex[:8]
        result_file = output_dir / f"interview_simulation_{session_id}.json"
        
        # Конвертируем в JSON-сериализуемый формат
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result.dict()
        
        # Сохраняем основной результат
        with result_file.open("w", encoding="utf-8") as f:
            json.dump(result_dict, f, ensure_ascii=False, indent=2)
        
        log.info(f"💾 Результат сохранен: {result_file}")
        
        # Сохраняем полный пайплайн (входные данные + результат + трейс)
        if trace and trace_file:
            pipeline_file = output_dir / f"full_pipeline_{session_id}.json"
            
            pipeline_data = {
                "pipeline_info": {
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "resume_source": str(resume_source) if resume_source else "fake_data",
                    "vacancy_source": str(vacancy_json),
                    "fake_llm": fake_llm,
                    "trace_enabled": trace
                },
                "input_data": {
                    "resume": result_dict.get("resume_info", {}),
                    "vacancy": result_dict.get("vacancy_info", {})
                },
                "simulation_result": result_dict,
                "trace_file": str(trace_file)
            }
            
            with pipeline_file.open("w", encoding="utf-8") as f:
                json.dump(pipeline_data, f, ensure_ascii=False, indent=2)
            
            print("\n📊 ПОЛНЫЙ ПАЙПЛАЙН СОХРАНЕН:")
            print(f"   Результат: {result_file}")
            print(f"   Трейс промптов: {trace_file}")
            print(f"   Полный пайплайн: {pipeline_file}")
        else:
            print(f"\n💾 Результат сохранен: {result_file}")
            if not trace:
                print("   💡 Используйте --trace для сохранения всех промптов")
        
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        log.error(f"❌ Ошибка генерации симуляции: {e}")
        import traceback
        traceback.print_exc()
        return 1


def create_sample_data():
    """Создает примерные данные для тестирования."""
    sample_resume = {
        "first_name": "Иван",
        "last_name": "Петров", 
        "title": "Python разработчик",
        "skills": "Опыт разработки веб-приложений на Python с использованием Django и FastAPI. Знание SQL, Git, Docker. Участие в проектах от архитектуры до деплоя.",
        "skill_set": ["Python", "Django", "FastAPI", "PostgreSQL", "Git", "Docker", "Redis", "REST API"],
        "experience": [
            {
                "company": "ООО ТехСофт",
                "position": "Python разработчик",
                "start": "2022-01",
                "end": "2024-12",
                "description": "Разработка и поддержка веб-приложений на Django. Проектирование архитектуры микросервисов. Оптимизация производительности. Код-ревью. Наставничество Junior разработчиков."
            },
            {
                "company": "ИП Сидоров",
                "position": "Junior Python разработчик", 
                "start": "2021-06",
                "end": "2021-12",
                "description": "Разработка REST API на FastAPI. Работа с PostgreSQL. Написание unit-тестов. Изучение Docker и DevOps практик."
            }
        ],
        "education": {
            "level": {"name": "Высшее"},
            "primary": [
                {
                    "name": "МГУ им. Ломоносова, Факультет ВМК",
                    "result": "Бакалавр прикладной математики и информатики",
                    "year": "2021"
                }
            ]
        },
        "total_experience": 36,
        "salary": {"amount": 150000},
        "professional_roles": [
            {"name": "Backend разработчик"},
            {"name": "Python Developer"}
        ],
        "languages": [
            {"name": "Русский", "level": {"name": "Родной"}},
            {"name": "Английский", "level": {"name": "B2 — Выше среднего"}}
        ],
        "contact": [
            {"type": {"name": "Эл. почта"}, "value": "ivan.petrov@example.com"}
        ],
        "site": [
            {"type": {"name": "GitHub"}, "url": "https://github.com/apetrov"}
        ],
        "employments": ["Полная занятость"],
        "schedules": ["Полный день"]
    }
    
    sample_vacancy = {
        "name": "Middle Python Developer",
        "company_name": "IT Solutions Ltd",
        "description": """
        <p>Мы ищем опытного Python разработчика для работы над крупными проектами в области финтех.</p>
        <h3>Требования:</h3>
        <ul>
            <li>Опыт коммерческой разработки на Python от 2-х лет</li>
            <li>Глубокое знание Django или FastAPI</li>
            <li>Опыт работы с PostgreSQL, знание SQL</li>
            <li>Понимание принципов REST API</li>
            <li>Знание Git, понимание Git Flow</li>
            <li>Опыт написания unit-тестов</li>
        </ul>
        <h3>Будет плюсом:</h3>
        <ul>
            <li>Опыт с Docker и Kubernetes</li>
            <li>Знание Redis</li>
            <li>Опыт с микросервисной архитектурой</li>
            <li>Знание JavaScript/TypeScript</li>
        </ul>
        <h3>Мы предлагаем:</h3>
        <ul>
            <li>Работу в команде профессионалов</li>
            <li>Интересные и сложные задачи</li>
            <li>Гибкий график работы</li>
            <li>Возможности для профессионального роста</li>
        </ul>
        """,
        "key_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "REST API", "Git", "Docker"],
        "professional_roles": [{"name": "Backend разработчик"}],
        "experience": {"id": "between1And3"},
        "employment": {"id": "full"},
        "schedule": {"id": "fullDay"}
    }
    
    # Создаем директорию если не существует
    data_dir = Path("tests/data")
    data_dir.mkdir(exist_ok=True)
    
    # Сохраняем примерные данные
    resume_file = data_dir / "sample_interview_resume.json"
    vacancy_file = data_dir / "sample_interview_vacancy.json"
    
    with resume_file.open("w", encoding="utf-8") as f:
        json.dump(sample_resume, f, ensure_ascii=False, indent=2)
    
    with vacancy_file.open("w", encoding="utf-8") as f:
        json.dump(sample_vacancy, f, ensure_ascii=False, indent=2)
    
    print("📝 Примерные данные созданы:")
    print(f"   Резюме: {resume_file}")
    print(f"   Вакансия: {vacancy_file}")
    
    return resume_file, vacancy_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Генерация симуляции интервью с полным трейсингом")
    parser.add_argument(
        "--resume-pdf", 
        type=Path, 
        help="Путь к PDF файлу резюме"
    )
    parser.add_argument(
        "--vacancy-json", 
        type=Path, 
        help="Путь к JSON файлу с вакансией"
    )
    parser.add_argument(
        "--fake-llm", 
        action="store_true", 
        help="Использовать fake LLM вместо OpenAI (для демо)"
    )
    parser.add_argument(
        "--trace", 
        action="store_true", 
        help="Включить полный трейсинг всех промптов и ответов"
    )
    parser.add_argument(
        "--create-sample", 
        action="store_true", 
        help="Создать примерные данные для тестирования"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Путь к YAML конфигурации (переопределяет встроенный config.yml)"
    )
    parser.add_argument(
        "--save-result",
        action="store_true",
        help="Сохранить результат в tests/data/ для PDF экспорта"
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        _, vacancy_file = create_sample_data()
        args.vacancy_json = vacancy_file
        args.resume_pdf = None  # Будет использован fake режим
        print("📝 Созданы тестовые данные. Будет использован fake режим для резюме.")
    
    if not args.vacancy_json:
        print("❌ Укажите путь к файлу вакансии или используйте --create-sample")
        print("Примеры:")
        print("  python examples/generate_interview_simulation.py --create-sample --fake-llm --trace")
        print("  python examples/generate_interview_simulation.py --resume-pdf resume.pdf --vacancy-json vacancy.json --trace")
        exit(1)
    
    # Устанавливаем путь к конфигу до импортов модулей симуляции
    if args.config:
        os.environ["INTERVIEW_SIM_CONFIG"] = str(args.config.expanduser())

    exit_code = asyncio.run(main(args.resume_pdf, args.vacancy_json, args.fake_llm, args.trace, getattr(args, 'save_result', False)))
    exit(exit_code)
