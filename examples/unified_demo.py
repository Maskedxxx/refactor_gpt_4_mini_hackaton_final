# examples/unified_demo_improved.py
# --- agent_meta ---
# role: unified-demo-application-v2
# owner: @backend
# contract: Улучшенный единый демо-скрипт с тестовым пользователем и реалистичными сценариями
# last_reviewed: 2025-08-24
# interfaces:
#   - CLI: python -m examples.unified_demo_improved --scenario full-demo
#   - CLI: python -m examples.unified_demo_improved --scenario test-user-setup
#   - CLI: python -m examples.unified_demo_improved --scenario hh-auth-demo
#   - CLI: python -m examples.unified_demo_improved --scenario feature-with-hash
#   - CLI: python -m examples.unified_demo_improved --scenario feature-no-hash
# --- /agent_meta ---

import argparse
import sys
import uuid
import json
import webbrowser
from pathlib import Path
from typing import Dict, Any

import httpx

from src.utils import init_logging_from_env, get_logger

init_logging_from_env()
logger = get_logger(__name__)


class ImprovedUnifiedDemo:
    """Улучшенный единый демо-класс с тестовым пользователем и реалистичными сценариями."""
    
    # Конфигурация доступных фич для тестового пользователя
    AVAILABLE_FEATURES = {
        "cover_letter": {
            "enabled": True,
            "description": "Генерация сопроводительного письма", 
            "endpoint": "/features/cover_letter/generate"
        },
        "gap_analyzer": {
            "enabled": True,
            "description": "Анализ пробелов в навыках",
            "endpoint": "/features/gap_analyzer/generate"
        },
        "interview_checklist": {
            "enabled": False,  # Отключено для демонстрации
            "description": "Чеклист для подготовки к интервью",
            "endpoint": "/features/interview_checklist/generate"
        },
        "interview_simulation": {
            "enabled": True,
            "description": "Симуляция интервью",
            "endpoint": "/features/interview_simulation/generate"
        }
    }
    
    # Тестовый пользователь (перезаписывается при каждом запуске)
    TEST_USER = {
        "email": "demo_user@testapp.com",
        "password": "demo123",
        "org_name": "Demo Test Organization"
    }
    
    # Тестовая вакансия для демонстрации
    TEST_VACANCY_URL = "https://hh.ru/vacancy/12345678"
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.email = self.TEST_USER["email"]
        self.password = self.TEST_USER["password"] 
        self.org_name = self.TEST_USER["org_name"]
        
        # HTTP клиент с timeout и редиректами
        self.client = httpx.Client(base_url=base_url, timeout=45.0, follow_redirects=True)
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        _ = exc_type, exc_val, exc_tb  # Suppress unused parameter warnings
        if hasattr(self, 'client'):
            self.client.close()
    
    def _load_test_data(self) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Загружает тестовые данные резюме и вакансии."""
        test_data_dir = Path("tests/data")
        
        with (test_data_dir / "simple_resume.json").open("r", encoding="utf-8") as f:
            resume_data = json.load(f)
        with (test_data_dir / "simple_vacancy.json").open("r", encoding="utf-8") as f:
            vacancy_data = json.load(f)
        
        return resume_data, vacancy_data
    
    def _find_feature_result_file(self, feature: str) -> Path | None:
        """Находит файл с результатом фичи по шаблону feature_result_*.json"""
        test_data_dir = Path("tests/data")
        
        # Исправляем название для gap_analyzer
        search_name = "gap_analysis" if feature == "gap_analyzer" else feature
        pattern = f"{search_name}_result_*.json"
        
        # Ищем файлы по паттерну
        matching_files = list(test_data_dir.glob(pattern))
        
        if matching_files:
            return matching_files[0]  # Возвращаем первый найденный
        
        return None
    
    def _show_feature_result_preview(self, feature: str, result_data: Dict[str, Any]) -> None:
        """Показывает краткий превью результата фичи."""
        print("\n📊 Result preview:")
        
        if feature == "cover_letter":
            subject = result_data.get('subject_line', 'N/A')
            content = result_data.get('content', '')
            print(f"   📧 Subject: {subject}")
            print(f"   📝 Length: {len(content)} chars")
            
            # Показываем первые 3 строки содержания
            if content:
                lines = content.split('\n')[:3]
                print("   📄 First lines:")
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        print(f"      {i}. {line.strip()[:100]}{'...' if len(line.strip()) > 100 else ''}")
                        
        elif feature == "gap_analyzer":
            gaps = result_data.get('skill_gaps', [])
            recommendations = result_data.get('recommendations', [])
            print(f"   📈 Skill gaps found: {len(gaps)}")
            print(f"   🎯 Recommendations: {len(recommendations)}")
            
            if gaps:
                print("   🔍 Top gaps:")
                for i, gap in enumerate(gaps[:3], 1):
                    skill_name = gap.get('skill_name', 'Unknown')
                    importance = gap.get('importance_level', 'N/A')
                    print(f"      {i}. {skill_name} (importance: {importance})")
                    
        elif feature == "interview_checklist":
            questions = result_data.get('questions', [])
            tips = result_data.get('preparation_tips', [])
            print(f"   ❓ Questions generated: {len(questions)}")
            print(f"   💡 Preparation tips: {len(tips)}")
            
            if questions:
                print("   📝 Sample questions:")
                for i, q in enumerate(questions[:3], 1):
                    question = q.get('question', 'N/A') if isinstance(q, dict) else str(q)
                    print(f"      {i}. {question[:80]}{'...' if len(question) > 80 else ''}")
                    
        elif feature == "interview_simulation":
            rounds = result_data.get('total_rounds_completed', 0)
            scenarios = result_data.get('scenarios', [])
            print(f"   💬 Interview rounds: {rounds}")
            print(f"   🎭 Scenarios: {len(scenarios)}")
            
            if scenarios:
                print("   🗺️ Sample scenarios:")
                for i, scenario in enumerate(scenarios[:2], 1):
                    name = scenario.get('scenario_name', 'Unknown') if isinstance(scenario, dict) else 'Unknown'
                    print(f"      {i}. {name}")
    
    def _setup_test_user(self) -> bool:
        """Настраивает тестового пользователя (перезаписывает если существует)."""
        print("\n[Setup] 👤 Setting up test user...")
        
        # Пробуем войти
        login_response = self.client.post("/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        
        if login_response.status_code == 200:
            print("ℹ️ Test user exists, overwriting with new session...")
            return True
        else:
            # Регистрируем нового
            signup_response = self.client.post("/auth/signup", json={
                "email": self.email,
                "password": self.password,
                "org_name": self.org_name
            })
            
            if signup_response.status_code == 200:
                print("✅ Test user created successfully")
                return True
            elif signup_response.status_code == 409:
                # Пользователь существует, логинимся
                login_response = self.client.post("/auth/login", json={
                    "email": self.email,
                    "password": self.password
                })
                if login_response.status_code == 200:
                    print("✅ Test user logged in successfully")
                    return True
            
            print("❌ Test user setup failed:", signup_response.status_code)
            return False
    
    def scenario_test_user_setup(self) -> int:
        """Сценарий: Настройка тестового пользователя"""
        print("👤 TEST USER SETUP DEMO")
        print(f"Base URL: {self.base_url}")
        print(f"Test User Email: {self.email}")
        print("=" * 60)
        
        if not self._setup_test_user():
            return 1
        
        # Получаем профиль
        me_response = self.client.get("/me")
        if me_response.status_code == 200:
            profile = me_response.json()
            print(f"\n✅ Test user profile:")
            print(f"   Email: {profile['user']['email']}")
            print(f"   User ID: {profile['user']['id']}")
            print(f"   Organization: {profile.get('org_id', 'N/A')}")
            
            # Показываем доступные фичи
            print(f"\n🧠 Available features for this user:")
            enabled_features = [name for name, config in self.AVAILABLE_FEATURES.items() if config["enabled"]]
            disabled_features = [name for name, config in self.AVAILABLE_FEATURES.items() if not config["enabled"]]
            
            print(f"   ✅ Enabled: {', '.join(enabled_features)}")
            print(f"   ❌ Disabled: {', '.join(disabled_features)}")
            
            return 0
        else:
            print("❌ Failed to get user profile")
            return 1
    
    def scenario_hh_auth_demo(self) -> int:
        """Сценарий: HH авторизация для тестового пользователя"""
        print("🔗 HH AUTHORIZATION DEMO")
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.email}")
        print("=" * 60)
        
        # Настраиваем пользователя
        if not self._setup_test_user():
            return 1
        
        # Проверяем статус HH
        print("\n[1] 🔍 Checking HH connection status...")
        hh_status_response = self.client.get("/auth/hh/status")
        
        if hh_status_response.status_code == 200:
            status_data = hh_status_response.json()
            print(f"📊 HH Status: {status_data}")
            
            if status_data.get("is_connected"):
                print("✅ HH already connected!")
                return 0
            else:
                print("⚠️ HH not connected, starting OAuth...")
        else:
            print(f"⚠️ Unable to check HH status: {hh_status_response.status_code}")
        
        # Запускаем HH OAuth
        print("\n[2] 🌐 Starting HH OAuth process...")
        hh_connect_response = self.client.get("/auth/hh/connect")
        
        if hh_connect_response.status_code == 200:
            connect_data = hh_connect_response.json()
            oauth_url = connect_data["auth_url"]
            
            print(f"🔗 OAuth URL: {oauth_url}")
            print("\n📱 Opening browser for HH authorization...")
            webbrowser.open(oauth_url)
            
            print("⏳ Complete the authorization in the browser")
            input("Press Enter after completing HH OAuth...")
            
            # Проверяем финальный статус
            print("\n[3] ✅ Verifying HH connection...")
            final_status_response = self.client.get("/auth/hh/status")
            
            if final_status_response.status_code == 200:
                final_status = final_status_response.json()
                if final_status.get("is_connected"):
                    print("✅ HH successfully connected!")
                    return 0
                else:
                    print("⚠️ HH connection not completed")
                    return 1
            else:
                print("⚠️ Unable to verify HH connection status")
                return 1
        else:
            print(f"❌ Failed to start HH OAuth: {hh_connect_response.status_code}")
            return 1
    
    def scenario_feature_with_hash(self, feature: str) -> int:
        """Сценарий: Запуск фичи с подгрузкой объектов по хешу"""
        print(f"🔄 FEATURE WITH HASH DEMO: {feature}")
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.email}")
        print("=" * 60)
        
        # Проверяем доступность фичи
        if not self.AVAILABLE_FEATURES.get(feature, {}).get("enabled", False):
            print(f"❌ Feature '{feature}' is not enabled for test user")
            enabled_features = [name for name, config in self.AVAILABLE_FEATURES.items() if config["enabled"]]
            print(f"💡 Available features: {', '.join(enabled_features)}")
            return 1
        
        # Настраиваем пользователя
        if not self._setup_test_user():
            return 1
        
        print("\n[1] 📁 Creating session to save objects in DB...")
        resume_data, vacancy_data = self._load_test_data()
        
        # Создаем первую сессию для сохранения хешей
        initial_session_response = self.client.post("/sessions/init_json", json={
            "resume": resume_data,
            "vacancy": vacancy_data,
            "reuse_by_hash": True
        })
        
        if initial_session_response.status_code != 200:
            print(f"❌ Initial session creation failed: {initial_session_response.status_code}")
            if initial_session_response.status_code == 401:
                print("   ⚠️ Requires HH authorization - run 'hh-auth-demo' first")
            return 1
        
        initial_session = initial_session_response.json()
        print(f"✅ Initial session created: {initial_session['session_id']}")
        
        print("\n[2] 🔄 Creating second session (should reuse objects by hash)...")
        
        # Создаем вторую сессию - должна использовать хеши
        hash_session_response = self.client.post("/sessions/init_json", json={
            "resume": resume_data,
            "vacancy": vacancy_data,
            "reuse_by_hash": True
        })
        
        if hash_session_response.status_code == 200:
            hash_session = hash_session_response.json()
            print(f"✅ Hash-based session created: {hash_session['session_id']}")
            print(f"📊 Resume reused: {hash_session['reused']['resume']}")
            print(f"📊 Vacancy reused: {hash_session['reused']['vacancy']}")
            
            if hash_session['reused']['resume'] and hash_session['reused']['vacancy']:
                print("\n🎉 SUCCESS: Objects loaded from DB by hash!")
            else:
                print("\n⚠️ Hash reuse partially worked")
        else:
            print(f"❌ Hash session creation failed: {hash_session_response.status_code}")
            return 1
        
        print(f"\n[3] 🚀 Simulating {feature} execution with hash-loaded objects...")
        
        # Имитируем выполнение фичи (загружаем готовый результат)
        result_file = self._find_feature_result_file(feature)
        if result_file:
            with result_file.open("r", encoding="utf-8") as f:
                mock_result = json.load(f)
            
            print(f"✅ Feature {feature} completed successfully!")
            self._show_feature_result_preview(feature, mock_result)
            print(f"\n📁 Full result loaded from: {result_file}")
            return 0
        else:
            print(f"❌ Test data not found for feature: {feature}")
            return 1
    
    def scenario_feature_no_hash(self, feature: str) -> int:
        """Сценарий: Запуск фичи с парсингом (когда хеш не найден)"""
        print(f"🔍 FEATURE WITHOUT HASH DEMO: {feature}")
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.email}")
        print("=" * 60)
        
        # Проверяем доступность фичи
        if not self.AVAILABLE_FEATURES.get(feature, {}).get("enabled", False):
            print(f"❌ Feature '{feature}' is not enabled for test user")
            enabled_features = [name for name, config in self.AVAILABLE_FEATURES.items() if config["enabled"]]
            print(f"💡 Available features: {', '.join(enabled_features)}")
            return 1
        
        # Настраиваем пользователя
        if not self._setup_test_user():
            return 1
        
        print("\n[1] 📄 Creating session via init_upload (simulates parsing)...")
        
        # Используем init_upload для имитации парсинга
        test_pdf_path = Path("tests/data/resume.pdf")
        if not test_pdf_path.exists():
            print(f"❌ Test PDF not found: {test_pdf_path}")
            print("💡 Using init_json as fallback...")
            
            # Fallback к init_json с отключенной дедупликацией
            resume_data, vacancy_data = self._load_test_data()
            upload_session_response = self.client.post("/sessions/init_json", json={
                "resume": resume_data,
                "vacancy": vacancy_data,
                "reuse_by_hash": False  # Отключаем дедупликацию
            })
        else:
            # Настоящий init_upload
            with open(test_pdf_path, "rb") as pdf_file:
                upload_session_response = self.client.post("/sessions/init_upload", data={
                    "vacancy_url": self.TEST_VACANCY_URL,
                    "reuse_by_hash": False,  # Принудительный парсинг
                    "ttl_sec": 3600
                }, files={
                    "resume_file": ("resume.pdf", pdf_file, "application/pdf")
                })
        
        if upload_session_response.status_code == 200:
            upload_session = upload_session_response.json()
            print(f"✅ Upload session created: {upload_session['session_id']}")
            print(f"📊 Resume reused: {upload_session['reused']['resume']} (should be False)")
            print(f"📊 Vacancy reused: {upload_session['reused']['vacancy']} (should be False)")
            
            if not upload_session['reused']['resume'] and not upload_session['reused']['vacancy']:
                print("\n🎉 SUCCESS: Objects were freshly parsed (no hash reuse)!")
            else:
                print("\n⚠️ Unexpected: some objects were reused despite reuse_by_hash=False")
        elif upload_session_response.status_code == 401:
            print("❌ Upload session creation failed: HH authorization required")
            print("   💡 Run 'hh-auth-demo' first")
            return 1
        else:
            print(f"❌ Upload session creation failed: {upload_session_response.status_code}")
            return 1
        
        print(f"\n[2] 🚀 Simulating {feature} execution with freshly parsed objects...")
        
        # Имитируем выполнение фичи (загружаем готовый результат)
        result_file = self._find_feature_result_file(feature)
        if result_file:
            with result_file.open("r", encoding="utf-8") as f:
                mock_result = json.load(f)
            
            print(f"✅ Feature {feature} completed successfully!")
            self._show_feature_result_preview(feature, mock_result)
            print(f"\n📁 Full result loaded from: {result_file}")
            return 0
        else:
            print(f"❌ Test data not found for feature: {feature}")
            return 1
    
    def scenario_full_demo(self) -> int:
        """Сценарий: Полная демонстрация всех возможностей"""
        print("🚀 FULL STACK DEMO")
        print(f"Base URL: {self.base_url}")
        print(f"Test User: {self.email}")
        print("=" * 60)
        
        print("\n🎯 Demo Plan:")
        print("1. Setup test user")
        print("2. Show available features")
        print("3. HH authorization")
        print("4. Feature with hash reuse")
        print("5. Feature without hash (parsing)")
        print("=" * 60)
        
        # Этап 1: Настройка пользователя
        print("\n[STEP 1] 👤 Test User Setup...")
        if not self._setup_test_user():
            return 1
        
        # Этап 2: Показ доступных фич
        print("\n[STEP 2] 📋 Available Features...")
        enabled_features = [name for name, config in self.AVAILABLE_FEATURES.items() if config["enabled"]]
        print(f"✅ Enabled features: {', '.join(enabled_features)}")
        
        # Этап 3: HH авторизация (опционально)
        print("\n[STEP 3] 🔗 HH Authorization...")
        hh_status_response = self.client.get("/auth/hh/status")
        if hh_status_response.status_code == 200:
            status_data = hh_status_response.json()
            if not status_data.get("is_connected"):
                print("⚠️ HH not connected. For full demo, please run:")
                print(f"   python examples/unified_demo_improved.py --scenario hh-auth-demo")
                print("⏩ Skipping HH-dependent steps...")
                return 0
            else:
                print("✅ HH already connected!")
        
        # Этап 4: Фича с хешем
        print("\n[STEP 4] 🔄 Feature with Hash Reuse...")
        test_feature = enabled_features[0] if enabled_features else "cover_letter"
        result = self.scenario_feature_with_hash(test_feature)
        if result != 0:
            print(f"⚠️ Hash demo failed, but continuing...")
        
        # Этап 5: Фича без хеша
        print("\n[STEP 5] 🔍 Feature without Hash (Parsing)...")
        result = self.scenario_feature_no_hash(test_feature)
        if result != 0:
            print(f"⚠️ No-hash demo failed, but demo completed...")
        
        print("\n" + "=" * 60)
        print("🎉 FULL DEMO COMPLETED!")
        print("=" * 60)
        return 0


def main(argv: list[str]) -> int:
    """Основная функция для запуска демо-сценариев."""
    parser = argparse.ArgumentParser(
        description="Improved Unified Demo - реалистичные сценарии с тестовым пользователем",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:

1. Полная демонстрация всех возможностей:
   python examples/unified_demo_improved.py --scenario full-demo

2. Настройка тестового пользователя:
   python examples/unified_demo_improved.py --scenario test-user-setup

3. HH авторизация:
   python examples/unified_demo_improved.py --scenario hh-auth-demo

4. Фича с загрузкой по хешу:
   python examples/unified_demo_improved.py --scenario feature-with-hash --feature cover_letter

5. Фича с парсингом (без хеша):
   python examples/unified_demo_improved.py --scenario feature-no-hash --feature gap_analyzer

ОСОБЕННОСТИ:
- Тестовый пользователь: demo_user@testapp.com (перезаписывается при каждом запуске)
- Настраиваемые права доступа к фичам в коде
- Реалистичная имитация хеш-дедупликации
- Демонстрация /sessions/init_upload vs /sessions/init_json

ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ:
- Запущенное приложение: uvicorn src.webapp.app:app --host 0.0.0.0 --port 8080
- Настроенные переменные окружения для HH API
- Тестовые данные в tests/data/
        """
    )
    
    parser.add_argument(
        "--scenario", 
        required=True,
        choices=["full-demo", "test-user-setup", "hh-auth-demo", "feature-with-hash", "feature-no-hash"],
        help="Выберите сценарий демонстрации"
    )
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8080",
        help="Base URL приложения (по умолчанию: http://localhost:8080)"
    )
    parser.add_argument(
        "--feature", 
        choices=["cover_letter", "gap_analyzer", "interview_checklist", "interview_simulation"],
        help="Фича для тестирования (для feature-* сценариев)"
    )
    
    args = parser.parse_args(argv)
    
    # Валидация аргументов
    if args.scenario in ["feature-with-hash", "feature-no-hash"] and not args.feature:
        print(f"❌ Scenario '{args.scenario}' requires --feature parameter")
        return 1
    
    # Запуск демо
    with ImprovedUnifiedDemo(args.base_url) as demo:
        if args.scenario == "full-demo":
            return demo.scenario_full_demo()
        elif args.scenario == "test-user-setup":
            return demo.scenario_test_user_setup()
        elif args.scenario == "hh-auth-demo":
            return demo.scenario_hh_auth_demo()
        elif args.scenario == "feature-with-hash":
            return demo.scenario_feature_with_hash(args.feature)
        elif args.scenario == "feature-no-hash":
            return demo.scenario_feature_no_hash(args.feature)
        else:
            print(f"❌ Unknown scenario: {args.scenario}")
            return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))