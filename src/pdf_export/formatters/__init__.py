# src/pdf_export/formatters/__init__.py
# --- agent_meta ---
# role: pdf-formatters-package
# owner: @backend
# contract: PDF форматтеры для различных LLM фич
# last_reviewed: 2025-08-17
# interfaces:
#   - AbstractPDFFormatter
#   - GapAnalyzerPDFFormatter
# --- /agent_meta ---

from .base import AbstractPDFFormatter
from .gap_analyzer import GapAnalyzerPDFFormatter
from .cover_letter import CoverLetterPDFFormatter

__all__ = ["AbstractPDFFormatter", "GapAnalyzerPDFFormatter", "CoverLetterPDFFormatter"]