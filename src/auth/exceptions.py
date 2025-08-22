# src/auth/exceptions.py
# --- agent_meta ---
# role: auth-exceptions
# owner: @backend
# contract: Кастомные типы исключений для модуля аутентификации
# last_reviewed: 2025-08-22
# interfaces:
#   - AuthenticationError: базовое исключение для проблем аутентификации
#   - UserExistsError: пользователь уже существует
#   - InvalidCredentialsError: неверные учетные данные
#   - SessionExpiredError: сессия истекла или недействительна
# --- /agent_meta ---

from typing import Optional


class AuthenticationError(Exception):
    """Базовое исключение для всех ошибок аутентификации."""
    
    def __init__(self, message: str, error_code: Optional[str] = None) -> None:
        super().__init__(message)
        self.error_code = error_code or "AUTH_ERROR"


class UserExistsError(AuthenticationError):
    """Пользователь с таким email уже существует."""
    
    def __init__(self, email: str) -> None:
        super().__init__(f"User with email '{email}' already exists", "USER_EXISTS")
        self.email = email


class InvalidCredentialsError(AuthenticationError):
    """Неверные учетные данные для входа."""
    
    def __init__(self, email: str) -> None:
        super().__init__("Invalid email or password", "INVALID_CREDENTIALS")
        self.email = email


class SessionExpiredError(AuthenticationError):
    """Сессия истекла или недействительна."""
    
    def __init__(self, session_id: Optional[str] = None) -> None:
        super().__init__("Session expired or invalid", "SESSION_EXPIRED")
        self.session_id = session_id