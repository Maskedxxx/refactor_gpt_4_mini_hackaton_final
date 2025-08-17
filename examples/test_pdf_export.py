# examples/test_pdf_export.py
# --- agent_meta ---
# role: pdf-export-example
# owner: @backend
# contract: Пример тестирования PDF экспорта с сохраненными результатами GAP анализа
# last_reviewed: 2025-08-17
# interfaces:
#   - main(result_file: str) -> int
# --- /agent_meta ---

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.pdf_export.service import PDFExportService
from src.pdf_export.formatters import GapAnalyzerPDFFormatter
from src.utils import get_logger

log = get_logger("examples.test_pdf_export")


async def run_async(result_file: str) -> int:
    """Тестирование PDF экспорта с сохраненным результатом GAP анализа."""
    
    # Загрузка сохраненного результата
    test_data_dir = Path("tests/data")
    result_path = test_data_dir / result_file
    
    if not result_path.exists():
        print("❌ Файл не найден: {result_path}")
        print("💡 Сгенерируйте результат командой:")
        print("   python -m examples.generate_gap_analysis --save-result")
        return 1
    
    with result_path.open("r", encoding="utf-8") as f:
        gap_result = json.load(f)
    
    log.info("Загружен GAP результат из %s", result_path)
    
    # Подготовка метаданных
    metadata = {
        "feature_name": "gap_analyzer",
        "version": "v1",
        "generated_at": datetime.now().isoformat(),
        "source_file": str(result_path)
    }
    
    # Инициализация PDF сервиса
    pdf_service = PDFExportService()
    formatter = GapAnalyzerPDFFormatter()
    
    # Генерация PDF
    log.info("Генерация PDF...")
    pdf_bytes = await pdf_service.generate_pdf(
        formatter=formatter,
        data=gap_result,
        metadata=metadata
    )
    
    # Сохранение PDF файла
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    pdf_filename = formatter.get_filename(metadata)
    pdf_path = output_dir / pdf_filename
    
    with pdf_path.open("wb") as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF успешно сгенерирован!")
    print(f"📁 Файл: {pdf_path}")
    print(f"📊 Размер: {len(pdf_bytes):,} байт")
    print(f"🎯 GAP анализ: {gap_result.get('overall_match_percentage', 'N/A')}% соответствие")
    
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Тестирование PDF экспорта GAP анализа")
    p.add_argument("--result-file", type=str, help="Имя файла с результатом в tests/data/")
    args = p.parse_args()
    
    if not args.result_file:
        # Автопоиск последнего файла результата
        test_data_dir = Path("tests/data")
        gap_files = list(test_data_dir.glob("gap_analysis_result_*.json"))
        
        if not gap_files:
            print("❌ Нет сохраненных результатов GAP анализа")
            print("💡 Сгенерируйте результат командой:")
            print("   python -m examples.generate_gap_analysis --save-result")
            return 1
        
        # Берем последний по времени создания
        latest_file = max(gap_files, key=lambda p: p.stat().st_mtime)
        args.result_file = latest_file.name
        print(f"🔍 Автовыбор файла: {args.result_file}")
    
    return asyncio.run(run_async(args.result_file))


if __name__ == "__main__":
    raise SystemExit(main())