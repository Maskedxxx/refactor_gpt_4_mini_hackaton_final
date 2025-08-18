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
from src.pdf_export.formatters import GapAnalyzerPDFFormatter, CoverLetterPDFFormatter, InterviewChecklistPDFFormatter
from src.utils import get_logger

log = get_logger("examples.test_pdf_export")


async def run_async(result_file: str, feature_name: str = "gap_analyzer") -> int:
    """Тестирование PDF экспорта с сохраненным результатом LLM фичи."""
    
    # Загрузка сохраненного результата
    test_data_dir = Path("tests/data")
    result_path = test_data_dir / result_file
    
    if not result_path.exists():
        print(f"❌ Файл не найден: {result_path}")
        print("💡 Сгенерируйте результат командой:")
        if feature_name == "gap_analyzer":
            print("   python -m examples.generate_gap_analysis --fake-llm --save-result")
        elif feature_name == "cover_letter":
            print("   python -m examples.generate_cover_letter --fake-llm --save-result")
        elif feature_name == "interview_checklist":
            print("   python -m examples.generate_interview_checklist --fake-llm --save-result")
        return 1
    
    with result_path.open("r", encoding="utf-8") as f:
        feature_result = json.load(f)
    
    log.info("Загружен результат %s из %s", feature_name, result_path)
    
    # Подготовка метаданных
    metadata = {
        "feature_name": feature_name,
        "version": "v1",
        "generated_at": datetime.now().isoformat(),
        "source_file": str(result_path)
    }
    
    # Выбор форматтера по типу фичи
    formatters = {
        "gap_analyzer": GapAnalyzerPDFFormatter(),
        "cover_letter": CoverLetterPDFFormatter(),
        "interview_checklist": InterviewChecklistPDFFormatter(),
    }
    
    formatter = formatters.get(feature_name)
    if not formatter:
        print(f"❌ Неподдерживаемая фича: {feature_name}")
        print(f"💡 Доступные фичи: {', '.join(formatters.keys())}")
        return 1
    
    # Инициализация PDF сервиса
    pdf_service = PDFExportService()
    
    # Генерация PDF
    log.info("Генерация PDF...")
    pdf_bytes = await pdf_service.generate_pdf(
        formatter=formatter,
        data=feature_result,
        metadata=metadata
    )
    
    # Сохранение PDF файла
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    pdf_filename = formatter.get_filename(metadata)
    pdf_path = output_dir / pdf_filename
    
    with pdf_path.open("wb") as f:
        f.write(pdf_bytes)
    
    print("✅ PDF успешно сгенерирован!")
    print(f"📁 Файл: {pdf_path}")
    print(f"📊 Размер: {len(pdf_bytes):,} байт")
    
    # Специфичная информация в зависимости от фичи
    if feature_name == "gap_analyzer":
        match_pct = feature_result.get('overall_match_percentage', 'N/A')
        print(f"🎯 Соответствие: {match_pct}%")
    elif feature_name == "cover_letter":
        quality_scores = feature_result.get('personalization_score', 'N/A')
        print(f"🎯 Персонализация: {quality_scores}/10")
    elif feature_name == "interview_checklist":
        total_time = feature_result.get('time_estimates', {}).get('total_time_needed', 'N/A')
        print(f"⏳ Общее время подготовки: {total_time}")
    
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Тестирование PDF экспорта LLM фич")
    p.add_argument("--result-file", type=str, help="Имя файла с результатом в tests/data/")
    p.add_argument("--feature", type=str, choices=["gap_analyzer", "cover_letter", "interview_checklist"], 
                   default="gap_analyzer", help="Тип фичи для PDF экспорта")
    args = p.parse_args()
    
    if not args.result_file:
        # Автопоиск последнего файла результата для выбранной фичи
        test_data_dir = Path("tests/data")
        pattern = f"{args.feature.replace('_', '_')}_result_*.json"
        feature_files = list(test_data_dir.glob(pattern))
        
        if not feature_files:
            print(f"❌ Нет сохраненных результатов для {args.feature}")
            print("💡 Сгенерируйте результат командой:")
            if args.feature == "gap_analyzer":
                print("   python -m examples.generate_gap_analysis --fake-llm --save-result")
            elif args.feature == "cover_letter":
                print("   python -m examples.generate_cover_letter --fake-llm --save-result")
            elif args.feature == "interview_checklist":
                print("   python -m examples.generate_interview_checklist --fake-llm --save-result")
            return 1
        
        # Берем последний по времени создания
        latest_file = max(feature_files, key=lambda p: p.stat().st_mtime)
        args.result_file = latest_file.name
        print(f"🔍 Автовыбор файла: {args.result_file}")
    
    return asyncio.run(run_async(args.result_file, args.feature))


if __name__ == "__main__":
    raise SystemExit(main())