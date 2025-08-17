# src/pdf_export/formatters/base.py
# --- agent_meta ---
# role: pdf-formatter-base
# owner: @backend
# contract: Абстрактный базовый класс для PDF форматтеров LLM результатов
# last_reviewed: 2025-08-17
# interfaces:
#   - AbstractPDFFormatter
# --- /agent_meta ---

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any


class AbstractPDFFormatter(ABC):
    """Базовый класс для форматтеров PDF отчетов LLM фич."""
    
    @property
    @abstractmethod
    def feature_name(self) -> str:
        """Название фичи для выбора шаблона."""
        ...
    
    @property
    @abstractmethod
    def template_name(self) -> str:
        """Имя Jinja2 шаблона для рендеринга."""
        ...
    
    @abstractmethod
    def prepare_context(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Подготовить контекст для рендеринга шаблона из Pydantic данных.
        
        Args:
            data: Словарь с результатом работы LLM фичи (model_dump())
            metadata: Метаданные генерации (feature_name, version, generated_at)
            
        Returns:
            Контекст для Jinja2 шаблона
        """
        ...
    
    def get_filename(self, metadata: Dict[str, Any]) -> str:
        """Генерация имени файла для скачивания."""
        feature = metadata.get("feature_name", "report")
        timestamp = metadata.get("generated_at", "").replace(":", "_").replace("-", "_")[:16]
        return f"{feature}_{timestamp}.pdf"