# tests/pdf_export/test_integration.py
# --- agent_meta ---
# role: pdf-export-integration-tests
# owner: @backend
# contract: Integration тесты для PDF сервиса с форматтерами
# last_reviewed: 2025-08-17
# interfaces:
#   - test_pdf_service_generate_*()
#   - test_error_handling_*()
#   - test_template_rendering_*()
# --- /agent_meta ---

import tempfile
import os
from pathlib import Path
from typing import Dict, Any

import pytest

from src.pdf_export.service import PDFExportService
from src.pdf_export.formatters import GapAnalyzerPDFFormatter, CoverLetterPDFFormatter


class TestPDFServiceIntegration:
    """Integration тесты для PDF сервиса с реальными форматтерами."""
    
    @pytest.mark.asyncio
    async def test_generate_gap_analyzer_pdf(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        """Тест генерации PDF для GAP анализа."""
        # Подготавливаем метаданные специфично для gap_analyzer
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}
        
        # Генерируем PDF
        pdf_content = await pdf_service.generate_pdf(
            feature_name="gap_analyzer",
            data=sample_gap_analysis_data,
            metadata=metadata
        )
        
        # Проверяем, что получили PDF содержимое
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 1000  # PDF должен быть достаточно большим
        assert pdf_content.startswith(b"%PDF-")  # PDF файл начинается с %PDF-
        
        # Сохраняем во временный файл для проверки
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
        
        try:
            # Проверяем, что файл создался и не пустой
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 1000
        finally:
            # Убираем временный файл
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_generate_cover_letter_pdf(self, pdf_service, sample_cover_letter_data, sample_metadata):
        """Тест генерации PDF для сопроводительного письма."""
        # Подготавливаем метаданные специфично для cover_letter
        metadata = {**sample_metadata, "feature_name": "cover_letter"}
        
        # Генерируем PDF
        pdf_content = await pdf_service.generate_pdf(
            feature_name="cover_letter",
            data=sample_cover_letter_data,
            metadata=metadata
        )
        
        # Проверяем, что получили PDF содержимое
        assert isinstance(pdf_content, bytes)
        assert len(pdf_content) > 1000
        assert pdf_content.startswith(b"%PDF-")
        
        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = tmp.name
        
        try:
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 1000
        finally:
            os.unlink(tmp_path)
    
    @pytest.mark.asyncio
    async def test_unknown_feature_error(self, pdf_service, sample_metadata):
        """Тест обработки ошибки при неизвестной фиче."""
        with pytest.raises(ValueError, match="Formatter for feature 'unknown_feature' not found"):
            await pdf_service.generate_pdf(
                feature_name="unknown_feature",
                data={},
                metadata=sample_metadata
            )
    
    @pytest.mark.asyncio
    async def test_invalid_data_error(self, pdf_service, sample_metadata):
        """Тест обработки ошибки при некорректных данных."""
        # Передаем пустые данные для gap_analyzer
        with pytest.raises(Exception):  # Может быть KeyError или другая ошибка
            await pdf_service.generate_pdf(
                feature_name="gap_analyzer",
                data={},  # Пустые данные должны вызвать ошибку
                metadata=sample_metadata
            )


class TestTemplateRendering:
    """Тесты рендеринга шаблонов с реальными данными."""
    
    @pytest.mark.asyncio
    async def test_gap_analyzer_template_content(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        """Тест содержимого рендеринга шаблона GAP анализа."""
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}
        
        pdf_content = await pdf_service.generate_pdf(
            feature_name="gap_analyzer",
            data=sample_gap_analysis_data,
            metadata=metadata
        )
        
        # PDF содержимое должно быть валидным
        assert pdf_content.startswith(b"%PDF-")
        
        # Примечание: для более детальной проверки содержимого PDF
        # потребовались бы специализированные библиотеки типа pdfplumber
        # Здесь проверяем только базовую валидность PDF
    
    @pytest.mark.asyncio
    async def test_cover_letter_template_content(self, pdf_service, sample_cover_letter_data, sample_metadata):
        """Тест содержимого рендеринга шаблона сопроводительного письма."""
        metadata = {**sample_metadata, "feature_name": "cover_letter"}
        
        pdf_content = await pdf_service.generate_pdf(
            feature_name="cover_letter",
            data=sample_cover_letter_data,
            metadata=metadata
        )
        
        # PDF содержимое должно быть валидным
        assert pdf_content.startswith(b"%PDF-")
    
    def test_template_files_exist(self):
        """Тест существования файлов шаблонов."""
        # Проверяем, что шаблоны существуют
        templates_dir = Path("src/pdf_export/templates")
        
        gap_template = templates_dir / "gap_analyzer.html"
        cover_template = templates_dir / "cover_letter.html"
        
        assert gap_template.exists(), f"GAP анализа шаблон не найден: {gap_template}"
        assert cover_template.exists(), f"Cover letter шаблон не найден: {cover_template}"
        
        # Проверяем, что файлы не пустые
        assert gap_template.stat().st_size > 100
        assert cover_template.stat().st_size > 100
    
    def test_style_files_exist(self):
        """Тест существования файлов стилей."""
        styles_dir = Path("src/pdf_export/styles")
        
        gap_style = styles_dir / "gap_analyzer.css"
        cover_style = styles_dir / "cover_letter.css"
        
        assert gap_style.exists(), f"GAP анализа стили не найдены: {gap_style}"
        assert cover_style.exists(), f"Cover letter стили не найдены: {cover_style}"
        
        # Проверяем, что файлы не пустые
        assert gap_style.stat().st_size > 100
        assert cover_style.stat().st_size > 100


class TestFormatterRegistration:
    """Тесты регистрации форматтеров в сервисе."""
    
    def test_formatters_registered(self, pdf_service):
        """Тест регистрации всех необходимых форматтеров."""
        # Проверяем, что форматтеры зарегистрированы
        assert "gap_analyzer" in pdf_service._formatters_registry
        assert "cover_letter" in pdf_service._formatters_registry
        
        # Проверяем типы форматтеров
        gap_formatter = pdf_service._formatters_registry["gap_analyzer"]
        cover_formatter = pdf_service._formatters_registry["cover_letter"]
        
        assert isinstance(gap_formatter, GapAnalyzerPDFFormatter)
        assert isinstance(cover_formatter, CoverLetterPDFFormatter)
    
    def test_formatter_properties(self, pdf_service):
        """Тест свойств зарегистрированных форматтеров."""
        gap_formatter = pdf_service._formatters_registry["gap_analyzer"]
        cover_formatter = pdf_service._formatters_registry["cover_letter"]
        
        # Проверяем базовые свойства
        assert gap_formatter.feature_name == "gap_analyzer"
        assert gap_formatter.template_name == "gap_analyzer.html"
        
        assert cover_formatter.feature_name == "cover_letter"
        assert cover_formatter.template_name == "cover_letter.html"


class TestPDFContentValidation:
    """Тесты валидации содержимого PDF."""
    
    @pytest.mark.asyncio
    async def test_pdf_size_reasonable(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        """Тест разумного размера PDF файла."""
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}
        
        pdf_content = await pdf_service.generate_pdf(
            feature_name="gap_analyzer",
            data=sample_gap_analysis_data,
            metadata=metadata
        )
        
        # PDF не должен быть слишком маленьким или слишком большим
        assert 1000 < len(pdf_content) < 10_000_000  # От 1KB до 10MB
    
    @pytest.mark.asyncio
    async def test_pdf_generation_consistency(self, pdf_service, sample_gap_analysis_data, sample_metadata):
        """Тест консистентности генерации PDF."""
        metadata = {**sample_metadata, "feature_name": "gap_analyzer"}
        
        # Генерируем PDF дважды с одинаковыми данными
        pdf_content_1 = await pdf_service.generate_pdf(
            feature_name="gap_analyzer",
            data=sample_gap_analysis_data,
            metadata=metadata
        )
        
        pdf_content_2 = await pdf_service.generate_pdf(
            feature_name="gap_analyzer",
            data=sample_gap_analysis_data,
            metadata=metadata
        )
        
        # Размеры должны быть примерно одинаковыми (могут незначительно отличаться из-за timestamp)
        size_diff = abs(len(pdf_content_1) - len(pdf_content_2))
        assert size_diff < 1000  # Разница не более 1KB
        
        # Оба должны быть валидными PDF
        assert pdf_content_1.startswith(b"%PDF-")
        assert pdf_content_2.startswith(b"%PDF-")