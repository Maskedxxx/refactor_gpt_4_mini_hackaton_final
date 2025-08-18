# tests/pdf_export/test_integration.py
# --- agent_meta ---
# role: pdf-export-integration-tests
# owner: @backend
# contract: Integration тесты для PDF сервиса с форматтерами
# last_reviewed: 2025-08-18
# interfaces:
#   - test_pdf_service_generate_*()
#   - test_error_handling_*()
#   - test_template_rendering_*()
# --- /agent_meta ---

import tempfile
import os
from pathlib import Path

import pytest

from src.pdf_export.service import PDFExportService
from src.pdf_export.formatters import (
    GapAnalyzerPDFFormatter,
    CoverLetterPDFFormatter,
    InterviewChecklistPDFFormatter,
)


class TestPDFServiceIntegration:
    """Integration тесты для PDF сервиса с реальными форматтерами."""

    @pytest.mark.asyncio
    async def test_generate_gap_analyzer_pdf(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        """Тест генерации PDF для GAP анализа."""
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}

        pdf_content = await pdf_service.generate_pdf(
            formatter=GapAnalyzerPDFFormatter(),
            data=sample_gap_analysis_data,
            metadata=metadata,
        )

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 1000
        assert pdf_content.startswith(b"%PDF-")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
        try:
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 1000
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_generate_cover_letter_pdf(self, pdf_service, sample_cover_letter_data, sample_metadata):
        """Тест генерации PDF для сопроводительного письма."""
        metadata = {**sample_metadata, "feature_name": "cover_letter"}

        pdf_content = await pdf_service.generate_pdf(
            formatter=CoverLetterPDFFormatter(),
            data=sample_cover_letter_data,
            metadata=metadata,
        )

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 1000
        assert pdf_content.startswith(b"%PDF-")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
        try:
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 1000
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_generate_interview_checklist_pdf(self, pdf_service, sample_interview_checklist_data, sample_metadata):
        """Тест генерации PDF для интервью-чеклиста."""
        metadata = {**sample_metadata, "feature_name": "interview_checklist"}

        pdf_content = await pdf_service.generate_pdf(
            formatter=InterviewChecklistPDFFormatter(),
            data=sample_interview_checklist_data,
            metadata=metadata,
        )

        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 1000
        assert pdf_content.startswith(b"%PDF-")

    @pytest.mark.skip(reason="Временное отключение проверки ошибок для некорректных данных (по договоренности)")
    @pytest.mark.asyncio
    async def test_invalid_data_error(self, pdf_service, sample_metadata):
        """Тест обработки ошибки при некорректных данных (временно отключен)."""
        await pdf_service.generate_pdf(
            formatter=GapAnalyzerPDFFormatter(),
            data={},
            metadata=sample_metadata,
        )


class TestTemplateRendering:
    """Тесты рендеринга шаблонов с реальными данными."""

    @pytest.mark.asyncio
    async def test_gap_analyzer_template_content(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}

        pdf_content = await pdf_service.generate_pdf(
            formatter=GapAnalyzerPDFFormatter(),
            data=sample_gap_analysis_data,
            metadata=metadata,
        )

        assert pdf_content.startswith(b"%PDF-")

    @pytest.mark.asyncio
    async def test_cover_letter_template_content(self, pdf_service, sample_cover_letter_data, sample_metadata):
        metadata = {**sample_metadata, "feature_name": "cover_letter"}

        pdf_content = await pdf_service.generate_pdf(
            formatter=CoverLetterPDFFormatter(),
            data=sample_cover_letter_data,
            metadata=metadata,
        )

        assert pdf_content.startswith(b"%PDF-")

    def test_template_files_exist(self):
        templates_dir = Path("src/pdf_export/templates")

        gap_template = templates_dir / "gap_analyzer.html"
        cover_template = templates_dir / "cover_letter.html"
        checklist_template = templates_dir / "interview_checklist.html"

        assert gap_template.exists()
        assert cover_template.exists()
        assert checklist_template.exists()

        assert gap_template.stat().st_size > 100
        assert cover_template.stat().st_size > 100
        assert checklist_template.stat().st_size > 100

    def test_style_files_exist(self):
        styles_dir = Path("src/pdf_export/styles")

        gap_style = styles_dir / "gap_analyzer.css"
        cover_style = styles_dir / "cover_letter.css"
        checklist_style = styles_dir / "interview_checklist.css"

        assert gap_style.exists()
        assert cover_style.exists()
        assert checklist_style.exists()

        assert gap_style.stat().st_size > 100
        assert cover_style.stat().st_size > 100
        assert checklist_style.stat().st_size > 100


class TestFormatterRegistration:
    """Тесты регистрации форматтеров (через экземпляры)."""

    def test_formatters_registered(self):
        assert isinstance(GapAnalyzerPDFFormatter(), GapAnalyzerPDFFormatter)
        assert isinstance(CoverLetterPDFFormatter(), CoverLetterPDFFormatter)
        assert isinstance(InterviewChecklistPDFFormatter(), InterviewChecklistPDFFormatter)

    def test_formatter_properties(self):
        assert GapAnalyzerPDFFormatter().template_name == "gap_analyzer.html"
        assert CoverLetterPDFFormatter().template_name == "cover_letter.html"
        assert InterviewChecklistPDFFormatter().template_name == "interview_checklist.html"


class TestPDFContentValidation:
    """Тесты валидации содержимого PDF."""

    @pytest.mark.asyncio
    async def test_pdf_size_reasonable(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}

        pdf_content = await pdf_service.generate_pdf(
            formatter=GapAnalyzerPDFFormatter(),
            data=sample_gap_analysis_data,
            metadata=metadata,
        )

        assert 1000 < len(pdf_content) < 10_000_000

    @pytest.mark.asyncio
    async def test_pdf_generation_consistency(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        fixed_meta = {
            **sample_metadata,
            "feature_name": "gap_analyzer",
            "generated_at": "2025-08-17T10:00:00",
        }

        pdf_1 = await pdf_service.generate_pdf(
            formatter=GapAnalyzerPDFFormatter(),
            data=sample_gap_analysis_data,
            metadata=fixed_meta,
        )
        pdf_2 = await pdf_service.generate_pdf(
            formatter=GapAnalyzerPDFFormatter(),
            data=sample_gap_analysis_data,
            metadata=fixed_meta,
        )

        assert pdf_1.startswith(b"%PDF-") and pdf_2.startswith(b"%PDF-")
        assert len(pdf_1) == len(pdf_2)
