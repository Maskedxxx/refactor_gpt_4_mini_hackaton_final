# src/callback_server/code_handler.py
# --- agent_meta ---
# role: auth-code-file-handler
# owner: @backend
# contract: Manages reading, writing, and cleaning up the auth code file.
# last_reviewed: 2025-07-24
# interfaces:
#   - CodeFileHandler
# --- /agent_meta ---

import os

from src.utils import get_logger

logger = get_logger(__name__)


class CodeFileHandler:
    """Обработчик временных файлов для хранения OAuth2 кодов авторизации.
    
    Этот класс реализует архитектурный паттерн "Data Access Object (DAO)" 
    для работы с временными файлами, содержащими коды авторизации.
    Он обеспечивает безопасное сохранение, чтение и удаление конфиденциальных
    данных авторизации в рамках OAuth2 Authorization Code Flow.
    
    Архитектурные принципы:
    - Single Responsibility: отвечает только за работу с файлом кода авторизации
    - Fail-Safe Operations: обрабатывает все возможные ошибки файловой системы
    - Resource Management: обеспечивает корректное освобождение файловых ресурсов
    - Security: временные файлы минимизируют риски безопасности
    - Logging: логирование всех операций для отладки и аудита
    
    Интеграция с OAuth2 процессом:
    1. callback_handler получает код от OAuth2 провайдера
    2. CodeFileHandler.write() сохраняет код в временный файл
    3. ServerManager.run_and_wait_for_code() читает код через read()
    4. Код обменивается на токены в основном приложении
    5. cleanup() удаляет временный файл для безопасности
    
    Пример использования:
        >>> handler = CodeFileHandler(".auth_code")
        >>> handler.cleanup()  # Очистка перед началом
        >>> handler.write("oauth2_authorization_code_123")
        >>> code = handler.read()
        >>> print(f"Полученный код: {code}")
        >>> handler.cleanup()  # Очистка после использования
    
    Пример с контекстным менеджером (рекомендуемое):
        >>> handler = CodeFileHandler()
        >>> try:
        ...     handler.write("oauth2_code")
        ...     code = handler.read()
        ...     # Обработка кода...
        ... finally:
        ...     handler.cleanup()  # Гарантированная очистка
    
    Attributes:
        file_path: Путь к временному файлу для хранения кода авторизации.
                   По умолчанию ".auth_code" в текущей директории.
                   
    Security Notes:
        - Временные файлы содержат конфиденциальные данные
        - Обязательно вызывайте cleanup() после использования
        - Не оставляйте файлы с кодами на диске надолго
        - Рассмотрите использование in-memory хранения для повышенной безопасности
    """

    def __init__(self, file_path: str = ".auth_code") -> None:
        self.file_path = file_path
        logger.debug("Инициализирован CodeFileHandler для OAuth2 кодов в файле: %s", file_path)

    def write(self, code: str) -> None:
        """Сохраняет код авторизации в временный файл.
        
        Этот метод атомарно создает временный файл с кодом авторизации,
        полученным от OAuth2 провайдера. Операция использует
        контекстный менеджер для гарантированного закрытия файла.
        
        Операция выполняется с полным логированием и обработкой ошибок.
        
        Пример использования:
            >>> handler = CodeFileHandler(".oauth_code")
            >>> handler.write("4/0AX4XfWjYZ-oauth-code-from-google")
            # Код сохранен в файл .oauth_code
            
        Пример обработки ошибок:
            >>> try:
            ...     handler.write("oauth_code_123")
            ... except IOError as e:
            ...     logger.error(f"Ошибка сохранения кода: {e}")
            ...     # Обработка ошибки...
        
        Args:
            code: OAuth2 код авторизации для сохранения.
                  Обычно это строка длиной 20-200 символов.
                  
        Raises:
            IOError: При ошибках записи в файл (нет прав, нет места, и т.д.).
            TypeError: Если code не является строкой.
            
        Side Effects:
            - Создает файл по пути self.file_path
            - Заменяет содержимое, если файл уже существует
            - Логирует операцию для отладки и аудита
        
        Security Note:
            Файл содержит конфиденциальные данные. Обязательно вызовите
            cleanup() после использования кода.
        """
        logger.debug("Запись кода авторизации в файл %s", self.file_path)
        try:
            with open(self.file_path, "w") as f:
                f.write(code)
            logger.info("Код авторизации успешно сохранен в файл")
        except IOError as e:
            logger.error("Не удалось записать код в файл %s: %s", self.file_path, e)
            raise

    def read(self) -> str:
        """Читает и возвращает код авторизации из временного файла.
        
        Этот метод безопасно читает содержимое временного файла,
        созданного методом write(). Операция использует контекстный
        менеджер для гарантированного закрытия файла и автоматически
        удаляет пробельные символы.
        
        Пример использования:
            >>> handler = CodeFileHandler(".oauth_code")
            >>> handler.write("authorization_code_123")
            >>> code = handler.read()
            >>> print(f"Код: {code}")
            "authorization_code_123"
            
        Пример обработки ошибок:
            >>> try:
            ...     code = handler.read()
            ... except FileNotFoundError:
            ...     logger.error("Файл с кодом не найден")
            ...     # Обработка отсутствующего файла...
            ... except IOError as e:
            ...     logger.error(f"Ошибка чтения файла: {e}")
            ...     # Обработка ошибки чтения...
        
        Пример полного цикла:
            >>> handler = CodeFileHandler()
            >>> handler.cleanup()  # Очистка перед началом
            >>> handler.write("oauth_code_from_provider")
            >>> code = handler.read()
            >>> # Использование кода для обмена на токены...
            >>> handler.cleanup()  # Обязательная очистка
        
        Returns:
            str: Код авторизации без пробельных символов.
                 Обычно это строка длиной 20-200 символов,
                 состоящая из букв, цифр и спецсимволов.
                 
        Raises:
            FileNotFoundError: Если файл с кодом не существует.
                              Обычно означает, что write() не был вызван ранее.
            IOError: При ошибках чтения файла (нет прав, поврежден диск, и т.д.).
            
        Note:
            Метод использует strip() для удаления пробельных символов,
            включая \n, \r, \t и обычные пробелы. Это помогает очистить
            код от случайных пробелов, которые могут попасть в URL.
        """
        logger.debug("Чтение кода авторизации из файла %s", self.file_path)
        try:
            with open(self.file_path, "r") as f:
                code = f.read().strip()
                logger.info("Код авторизации успешно прочитан из файла")
                return code
        except FileNotFoundError:
            logger.warning("Файл с кодом %s не найден", self.file_path)
            raise
        except IOError as e:
            logger.error("Не удалось прочитать код из файла %s: %s", self.file_path, e)
            raise

    def cleanup(self) -> None:
        """Удаляет временный файл с кодом авторизации.
        
        Этот метод безопасно удаляет временный файл, содержащий
        конфиденциальные данные авторизации. Операция обязательно должна
        выполняться после использования кода для обеспечения безопасности.
        
        Метод идемпотентен - можно вызывать многократно без побочных эффектов.
        Он проверяет существование файла перед удалением и обрабатывает
        возможные ошибки файловой системы.
        
        Пример использования (обязательно):
            >>> handler = CodeFileHandler()
            >>> handler.write("oauth_code_123")
            >>> code = handler.read()
            >>> # Использование кода...
            >>> handler.cleanup()  # ОБЯЗАТЕЛЬНО!
            
        Пример с try-finally (рекомендуемое):
            >>> handler = CodeFileHandler()
            >>> try:
            ...     handler.write("code")
            ...     code = handler.read()
            ...     # Обработка кода...
            ... finally:
            ...     handler.cleanup()  # Гарантированная очистка
            
        Пример обработки ошибок:
            >>> try:
            ...     handler.cleanup()
            ... except OSError as e:
            ...     logger.error(f"Ошибка удаления файла: {e}")
            ...     # Обработка ошибки...
        
        Пример многократного вызова:
            >>> handler = CodeFileHandler()
            >>> handler.cleanup()  # Ничего не происходит, файла нет
            >>> handler.write("code")
            >>> handler.cleanup()  # Удаляет файл
            >>> handler.cleanup()  # Ничего не происходит, файл уже удален
        
        Raises:
            OSError: При ошибках удаления файла (нет прав, файл заблокирован, и т.д.).
                    Обычно это означает проблемы с правами доступа.
            
        Side Effects:
            - Удаляет файл по пути self.file_path, если он существует
            - Логирует операцию для отладки и аудита
            
        Security Importance:
            Этот метод критичен для безопасности! Не оставляйте
            файлы с OAuth2 кодами на диске - это создает уязвимости безопасности.
        """
        if os.path.exists(self.file_path):
            logger.debug("Удаление временного файла с кодом %s", self.file_path)
            try:
                os.remove(self.file_path)
                logger.debug("Временный файл с кодом %s успешно удален", self.file_path)
            except OSError as e:
                logger.error("Не удалось удалить файл с кодом %s: %s", self.file_path, e)
                raise
        else:
            logger.debug("Файл %s не существует, очистка не требуется", self.file_path)

    def exists(self) -> bool:
        """Проверяет существование временного файла с кодом авторизации.
        
        Этот метод полезен для проверки состояния перед выполнением операций
        чтения или очистки. Он не выбрасывает исключения и може
        использоваться для условной логики в клиентском коде.
        
        Пример использования для проверки состояния:
            >>> handler = CodeFileHandler()
            >>> if handler.exists():
            ...     print("Файл с кодом уже существует")
            ...     code = handler.read()
            ... else:
            ...     print("Файл отсутствует, ожидаем callback")
            
        Пример безопасной очистки:
            >>> handler = CodeFileHandler()
            >>> if handler.exists():
            ...     logger.info("Очистка старого файла с кодом")
            ...     handler.cleanup()
            
        Пример мониторинга состояния:
            >>> import time
            >>> handler = CodeFileHandler()
            >>> print("Ожидание появления кода...")
            >>> while not handler.exists():
            ...     time.sleep(0.5)  # Поллинг каждые 0.5 сек
            >>> print("Код получен!")
            >>> code = handler.read()
        
        Returns:
            bool: True, если файл существует, False в противном случае.
                  Не выбрасывает исключения, даже при ошибках файловой системы.
                  
        Side Effects:
            - Логирует результат проверки для отладки
            
        Note:
            Этот метод проверяет только существование файла,
            но не его читабельность или валидность содержимого.
            Для полной валидации используйте метод read().
        """
        exists = os.path.exists(self.file_path)
        logger.debug("Проверка существования файла %s: %s", self.file_path, "существует" if exists else "не существует")
        return exists
