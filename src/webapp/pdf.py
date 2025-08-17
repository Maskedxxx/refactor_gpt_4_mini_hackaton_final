# src/webapp/pdf.py
# --- agent_meta ---
# role: webapp-pdf-export
# owner: @backend
# contract: FastAPI роуты для экспорта LLM результатов в PDF
# last_reviewed: 2025-08-17
# interfaces:
#   - POST /features/{feature_name}/export/pdf
# --- /agent_meta ---

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from src.utils import get_logger
from src.pdf_export.service import PDFExportService
from src.pdf_export.formatters import GapAnalyzerPDFFormatter

logger = get_logger(__name__)
router = APIRouter(prefix="/features", tags=["PDF Export"])

# Глобальный экземпляр сервиса PDF
_pdf_service = PDFExportService()

# Регистр форматтеров
_formatters_registry = {
    "gap_analyzer": GapAnalyzerPDFFormatter(),
}


class PDFExportRequest(BaseModel):
    """Запрос на экспорт LLM результата в PDF."""
    result: Dict[str, Any] = Field(..., description="Результат LLM фичи (model_dump())")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Метаданные генерации"
    )


@router.post("/{feature_name}/export/pdf")
async def export_feature_pdf(
    feature_name: str,
    request: PDFExportRequest
) -> Response:
    """Экспорт результата LLM фичи в PDF формат."""
    try:
        logger.info("Запрос PDF экспорта для фичи %s", feature_name)
        
        # 1. Получение форматтера
        formatter = _formatters_registry.get(feature_name)
        if not formatter:
            raise HTTPException(
                status_code=404, 
                detail=f"PDF export not supported for feature: {feature_name}"
            )
        
        # 2. Подготовка метаданных
        metadata = request.metadata.copy()
        metadata.setdefault("feature_name", feature_name)
        metadata.setdefault("generated_at", datetime.now().isoformat())
        
        # 3. Генерация PDF
        pdf_bytes = await _pdf_service.generate_pdf(
            formatter=formatter,
            data=request.result,
            metadata=metadata
        )
        
        # 4. Подготовка имени файла
        filename = formatter.get_filename(metadata)
        
        logger.info(
            "PDF успешно сгенерирован для %s: %d байт, файл=%s",
            feature_name, len(pdf_bytes), filename
        )
        
        # 5. Возврат PDF файла
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Ошибка PDF экспорта для %s: %s", feature_name, str(e))
        raise HTTPException(
            status_code=500,
            detail=f"PDF export failed: {str(e)}"
        )


@router.get("/{feature_name}/export/pdf/available")
async def check_pdf_export_availability(feature_name: str) -> Dict[str, bool]:
    """Проверить доступность PDF экспорта для фичи."""
    available = feature_name in _formatters_registry
    
    return {
        "pdf_export_available": available,
        "feature_name": feature_name
    }