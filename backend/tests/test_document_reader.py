from __future__ import annotations

from io import BytesIO
import base64

from app.schemas.material import MaterialParseRequest
from app.services.document_reader import read_document
from app.services.material_service import parse_material


def test_reads_real_csv_rows_numbers_and_months() -> None:
    content = "月份,收入,支出\n2026-01,1000,700\n2026-02,1200,750\n".encode("utf-8")

    result = read_document(content, "cashflow.csv")

    assert result.document_type == "CSV"
    assert result.row_count == 3
    assert result.numeric_cells == 4
    assert result.period_months == 2
    assert result.has_content is True


def test_reads_real_xlsx_without_persisting_file() -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["月份", "收入"])
    sheet.append(["2026-01", 1000])
    buffer = BytesIO()
    workbook.save(buffer)
    workbook.close()

    result = read_document(buffer.getvalue(), "cashflow.xlsx")

    assert result.document_type == "Excel"
    assert result.sheet_count == 1
    assert result.row_count == 2
    assert result.numeric_cells == 1
    assert result.period_months == 1


def test_image_is_explicitly_not_ocr_output() -> None:
    result = read_document(b"not-used-by-image-reader", "license.png")

    assert result.has_content is False
    assert "OCR" in result.warnings[0]


def test_non_demo_material_returns_real_bounded_extraction() -> None:
    content = "月份,收入\n2026-01,1000\n2026-02,1200\n".encode("utf-8")

    evidence = parse_material(
        MaterialParseRequest(
            merchant_id="M999",
            group="cashflow",
            file_name="cashflow.csv",
            media_type="text/csv",
            size_bytes=len(content),
            content_base64=base64.b64encode(content).decode("ascii"),
        )
    )

    assert evidence.simulated is False
    assert evidence.period_months == 2
    assert evidence.subject_match is False
    assert any(item.label == "有效行数" for item in evidence.extracted_metrics)
    assert all("1000" not in finding for finding in evidence.findings)
