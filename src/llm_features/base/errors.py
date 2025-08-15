# src/llm_features/base/errors.py
# --- agent_meta ---
# role: llm-features-errors
# owner: @backend
# contract: Базовые исключения для LLM-фич
# last_reviewed: 2025-08-15
# interfaces:
#   - BaseLLMError (базовое исключение)
#   - FeatureNotFoundError (фича не найдена)
#   - FeatureRegistrationError (ошибка регистрации)
# --- /agent_meta ---


class BaseLLMError(Exception):
    """Базовое исключение для всех LLM-фич."""
    pass


class FeatureNotFoundError(BaseLLMError):
    """Исключение при запросе несуществующей фичи."""
    def __init__(self, feature_name: str, version: str = None):
        if version:
            msg = f"Feature '{feature_name}' version '{version}' not found"
        else:
            msg = f"Feature '{feature_name}' not found"
        super().__init__(msg)
        self.feature_name = feature_name
        self.version = version


class FeatureRegistrationError(BaseLLMError):
    """Исключение при ошибке регистрации фичи."""
    def __init__(self, feature_name: str, reason: str):
        msg = f"Failed to register feature '{feature_name}': {reason}"
        super().__init__(msg)
        self.feature_name = feature_name
        self.reason = reason


class ValidationError(BaseLLMError):
    """Исключение при ошибке валидации результата."""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field


class PromptBuildError(BaseLLMError):
    """Исключение при ошибке сборки промпта."""
    pass