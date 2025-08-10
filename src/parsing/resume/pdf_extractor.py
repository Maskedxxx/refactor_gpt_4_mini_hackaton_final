# src/parsing/resume/pdf_extractor.py
# --- agent_meta ---
# role: resume-pdf-extractor
# owner: @backend
# contract: Извлечение текста из PDF для дальнейшего LLM-парсинга
# last_reviewed: 2025-08-10
# interfaces:
#   - IPDFExtractor.extract_text(src: str | bytes | Path) -> str
#   - PdfPlumberExtractor (реализация)
# --- /agent_meta ---

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union
import io

import pdfplumber
from src.utils import get_logger


class IPDFExtractor:
    def extract_text(self, src: Union[str, Path, bytes]) -> str:  # pragma: no cover - интерфейс
        raise NotImplementedError


class PdfPlumberExtractor(IPDFExtractor):
    """
    Экстрактор текста из PDF через pdfplumber. Поддерживает путь к файлу и bytes.
    """
    def __init__(self) -> None:
        self._log = get_logger(__name__)

    def extract_text(self, src: Union[str, Path, bytes]) -> str:
        if isinstance(src, (str, Path)):
            return self._extract_from_path(Path(src))
        elif isinstance(src, (bytes, bytearray)):
            return self._extract_from_bytes(bytes(src))
        else:
            raise TypeError("src должен быть путем к файлу или bytes")

    def _extract_from_path(self, path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"PDF файл не найден: {path}")
        self._log.info("Извлечение текста из PDF: %s", path)
        with pdfplumber.open(str(path)) as pdf:
            text_parts: list[str] = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text_parts.append(page_text)
            text = "\n".join(text_parts).strip()
            if not text:
                raise RuntimeError("Не удалось извлечь текст из PDF")
            self._log.info("Извлечено символов: %d", len(text))
            return text

    def _extract_from_bytes(self, data: bytes) -> str:
        self._log.info("Извлечение текста из PDF bytes (%d bytes)", len(data))
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text_parts: list[str] = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text:
                    text_parts.append(page_text)
            text = "\n".join(text_parts).strip()
            if not text:
                raise RuntimeError("Не удалось извлечь текст из PDF (bytes)")
            self._log.info("Извлечено символов: %d", len(text))
            return text
