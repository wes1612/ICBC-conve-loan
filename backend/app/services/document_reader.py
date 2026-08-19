"""Bounded local extraction for uploaded tabular and text documents.

This reader intentionally returns only compact diagnostics. Raw document text
is not persisted, logged, or sent to the language-model provider.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Iterable
from zipfile import BadZipFile, ZipFile


MAX_ARCHIVE_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_DOCUMENT_TEXT_CHARS = 20_000
MAX_SPREADSHEET_CELLS = 10_000
MAX_PDF_PAGES = 100


@dataclass(frozen=True)
class DocumentExtraction:
    document_type: str
    extracted_characters: int
    row_count: int = 0
    column_count: int = 0
    page_count: int = 0
    sheet_count: int = 0
    numeric_cells: int = 0
    period_months: int | None = None
    warnings: tuple[str, ...] = ()

    @property
    def has_content(self) -> bool:
        return self.extracted_characters > 0 or self.row_count > 0


def _validate_office_archive(content: bytes) -> None:
    try:
        with ZipFile(BytesIO(content)) as archive:
            infos = archive.infolist()
            if len(infos) > 2_000:
                raise ValueError("Office 文件包含过多内部条目")
            if sum(item.file_size for item in infos) > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError("Office 文件解压后超过 50 MB 安全上限")
    except BadZipFile as exc:
        raise ValueError("Office 文件压缩结构无效") from exc


def _decode_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030", "utf-16"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 文本编码无法识别，请使用 UTF-8 或 GB18030")


def _month_count(values: Iterable[Any]) -> int | None:
    months: set[str] = set()
    for value in values:
        if isinstance(value, (datetime, date)):
            months.add(value.strftime("%Y-%m"))
        elif isinstance(value, str):
            candidate = value.strip()[:10].replace("/", "-")
            if len(candidate) >= 7 and candidate[:4].isdigit() and candidate[4] == "-":
                months.add(candidate[:7])
    return len(months) or None


def _read_csv(content: bytes) -> DocumentExtraction:
    text = _decode_text(content)
    rows = csv.reader(StringIO(text))
    row_count = 0
    column_count = 0
    numeric_cells = 0
    sampled_values: list[Any] = []
    for row in rows:
        if row_count >= MAX_SPREADSHEET_CELLS:
            break
        if not any(cell.strip() for cell in row):
            continue
        row_count += 1
        column_count = max(column_count, len(row))
        for cell in row:
            value = cell.strip()
            if value:
                sampled_values.append(value)
                try:
                    float(value.replace(",", ""))
                except ValueError:
                    pass
                else:
                    numeric_cells += 1
    return DocumentExtraction(
        document_type="CSV",
        extracted_characters=min(len(text), MAX_DOCUMENT_TEXT_CHARS),
        row_count=row_count,
        column_count=column_count,
        numeric_cells=numeric_cells,
        period_months=_month_count(sampled_values),
    )


def _read_xlsx(content: bytes) -> DocumentExtraction:
    _validate_office_archive(content)
    from openpyxl import load_workbook

    workbook = load_workbook(BytesIO(content), read_only=True, data_only=True)
    row_count = 0
    column_count = 0
    numeric_cells = 0
    characters = 0
    sampled_values: list[Any] = []
    try:
        for sheet in workbook.worksheets[:20]:
            for row in sheet.iter_rows(values_only=True):
                values = [value for value in row if value not in (None, "")]
                if not values:
                    continue
                row_count += 1
                column_count = max(column_count, len(row))
                for value in values:
                    sampled_values.append(value)
                    characters += len(str(value))
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_cells += 1
                if len(sampled_values) >= MAX_SPREADSHEET_CELLS:
                    break
            if len(sampled_values) >= MAX_SPREADSHEET_CELLS:
                break
        return DocumentExtraction(
            document_type="Excel",
            extracted_characters=min(characters, MAX_DOCUMENT_TEXT_CHARS),
            row_count=row_count,
            column_count=column_count,
            sheet_count=len(workbook.sheetnames),
            numeric_cells=numeric_cells,
            period_months=_month_count(sampled_values),
        )
    finally:
        workbook.close()


def _read_xls(content: bytes) -> DocumentExtraction:
    import xlrd

    workbook = xlrd.open_workbook(file_contents=content, on_demand=True)
    row_count = 0
    column_count = 0
    numeric_cells = 0
    characters = 0
    sampled_values: list[Any] = []
    try:
        for sheet in workbook.sheets()[:20]:
            for row_index in range(min(sheet.nrows, MAX_SPREADSHEET_CELLS)):
                values = [value for value in sheet.row_values(row_index) if value not in (None, "")]
                if not values:
                    continue
                row_count += 1
                column_count = max(column_count, sheet.ncols)
                for value in values:
                    sampled_values.append(value)
                    characters += len(str(value))
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        numeric_cells += 1
                if len(sampled_values) >= MAX_SPREADSHEET_CELLS:
                    break
        return DocumentExtraction(
            document_type="Excel 97-2003",
            extracted_characters=min(characters, MAX_DOCUMENT_TEXT_CHARS),
            row_count=row_count,
            column_count=column_count,
            sheet_count=workbook.nsheets,
            numeric_cells=numeric_cells,
            period_months=_month_count(sampled_values),
        )
    finally:
        workbook.release_resources()


def _read_docx(content: bytes) -> DocumentExtraction:
    _validate_office_archive(content)
    from docx import Document

    document = Document(BytesIO(content))
    fragments = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    table_rows = 0
    for table in document.tables[:50]:
        for row in table.rows[:500]:
            table_rows += 1
            fragments.extend(cell.text for cell in row.cells if cell.text.strip())
    characters = sum(len(fragment) for fragment in fragments)
    return DocumentExtraction(
        document_type="Word",
        extracted_characters=min(characters, MAX_DOCUMENT_TEXT_CHARS),
        row_count=table_rows,
    )


def _read_pdf(content: bytes) -> DocumentExtraction:
    from pypdf import PdfReader

    # pypdf's non-strict mode accepts common producer quirks such as repaired
    # xref tables; signature, size and page-count checks still apply.
    reader = PdfReader(BytesIO(content), strict=False)
    if len(reader.pages) > MAX_PDF_PAGES:
        raise ValueError(f"PDF 页数不能超过 {MAX_PDF_PAGES} 页")
    characters = 0
    for page in reader.pages:
        characters += len(page.extract_text() or "")
        if characters >= MAX_DOCUMENT_TEXT_CHARS:
            break
    warnings: tuple[str, ...] = ()
    if characters == 0:
        warnings = ("PDF 未提取到文本，可能是扫描件，需要另接 OCR 服务",)
    return DocumentExtraction(
        document_type="PDF",
        extracted_characters=min(characters, MAX_DOCUMENT_TEXT_CHARS),
        page_count=len(reader.pages),
        warnings=warnings,
    )


def read_document(content: bytes, file_name: str) -> DocumentExtraction:
    extension = Path(file_name).suffix.lower()
    try:
        if extension == ".csv":
            return _read_csv(content)
        if extension == ".xlsx":
            return _read_xlsx(content)
        if extension == ".xls":
            return _read_xls(content)
        if extension == ".docx":
            return _read_docx(content)
        if extension == ".pdf":
            return _read_pdf(content)
        if extension in {".png", ".jpg", ".jpeg"}:
            return DocumentExtraction(
                document_type="图片",
                extracted_characters=0,
                warnings=("图片已通过格式校验，但当前未配置 OCR，尚未读取图片文字",),
            )
        raise ValueError(f"尚不支持读取 {extension or '无扩展名'} 文件")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"{extension or '该'} 文件结构无法安全读取") from exc
