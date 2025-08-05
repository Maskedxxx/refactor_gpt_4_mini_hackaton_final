# src/hh_adapter/__main__.py
# --- agent_meta ---
# role: component-demo-runner
# owner: @backend
# contract: Provides a CLI entry point to demonstrate the HH.ru auth URL generation.
# last_reviewed: 2025-08-05
# dependencies: [src.hh_adapter.auth, src.hh_adapter.config]
# --- /agent_meta ---

from src.hh_adapter.auth import HHAuthService
from src.hh_adapter.config import HHSettings
from src.utils import get_logger

logger = get_logger(__name__)

def main():
    """Генерирует и выводит URL для авторизации HH.ru."""
    logger.info("Запуск hh_adapter в демонстрационном режиме...")
    
    try:
        settings = HHSettings()
        auth_service = HHAuthService(settings)
        auth_url = auth_service.get_auth_url()
        
        print("\n" + "="*70)
        print("Демонстрационный режим для HH Adapter")
        print("Ниже представлена ссылка для инициации OAuth2 авторизации на HH.ru.")
        print("\nПерейдите по этой ссылке в браузере:")
        print(f"\n  {auth_url}\n")
        print("После авторизации вы будете перенаправлены на redirect_uri,")
        print("где должен работать callback-сервер для перехвата кода.")
        print("="*70 + "\n")

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)
        print("\nОшибка: Не удалось создать URL. Убедитесь, что переменные окружения (HH_CLIENT_ID, HH_CLIENT_SECRET, HH_REDIRECT_URI) заданы в .env файле.")

if __name__ == "__main__":
    main()
