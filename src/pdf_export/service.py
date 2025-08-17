# src/pdf_export/service.py
# --- agent_meta ---
# role: pdf-export-service
# owner: @backend
# contract: Сервис генерации PDF из HTML шаблонов через WeasyPrint
# last_reviewed: 2025-08-17
# interfaces:
#   - PDFExportService
# --- /agent_meta ---

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Optional

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from src.utils import get_logger
from .formatters.base import AbstractPDFFormatter


class PDFExportService:
    """Сервис экспорта LLM результатов в PDF."""
    
    def __init__(self, templates_dir: Optional[Path] = None, styles_dir: Optional[Path] = None):
        self._log = get_logger(__name__)
        
        # Пути к шаблонам и стилям
        base_dir = Path(__file__).parent
        self._templates_dir = templates_dir or (base_dir / "templates")
        self._styles_dir = styles_dir or (base_dir / "styles")
        
        # Jinja2 окружение
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=True
        )
        
        # Кеш CSS
        self._css_cache: Dict[str, CSS] = {}
        
        self._log.info("PDF Export Service инициализирован: templates=%s", self._templates_dir)
    
    async def generate_pdf(
        self,
        formatter: AbstractPDFFormatter,
        data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> bytes:
        """Генерация PDF из данных LLM фичи."""
        try:
            self._log.info("Генерация PDF для фичи %s", formatter.feature_name)
            
            # 1. Подготовка контекста
            template_context = formatter.prepare_context(data, metadata)
            
            # 2. Рендеринг HTML
            template = self._jinja_env.get_template(formatter.template_name)
            html_content = template.render(**template_context)
            
            # 3. Загрузка CSS
            css_styles = self._get_css_for_feature(formatter.feature_name)
            
            # 4. Генерация PDF
            html_doc = HTML(string=html_content)
            pdf_bytes = html_doc.write_pdf(stylesheets=css_styles)
            
            self._log.info("PDF успешно сгенерирован для %s, размер: %d байт", 
                          formatter.feature_name, len(pdf_bytes))
            
            return pdf_bytes
            
        except Exception as e:
            self._log.error("Ошибка генерации PDF для %s: %s", formatter.feature_name, str(e))
            raise
    
    def _get_css_for_feature(self, feature_name: str) -> list[CSS]:
        """Получить CSS стили для фичи (с кешированием)."""
        cache_key = feature_name
        
        if cache_key not in self._css_cache:
            css_files = []
            
            # Базовые стили
            base_css = self._styles_dir / "base.css"
            if base_css.exists():
                css_files.append(CSS(filename=str(base_css)))
            
            # Специфичные стили фичи
            feature_css = self._styles_dir / f"{feature_name}.css"
            if feature_css.exists():
                css_files.append(CSS(filename=str(feature_css)))
                
            self._css_cache[cache_key] = css_files
            self._log.debug("CSS загружен для %s: %d файлов", feature_name, len(css_files))
        
        return self._css_cache[cache_key]