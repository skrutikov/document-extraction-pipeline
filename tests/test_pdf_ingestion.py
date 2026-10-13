from pathlib import Path

import pymupdf
import pytest

from document_extraction_pipeline.ingestion.pdf import (
    DocumentIngestionError,
    ingest_pdf,
)


def test_extracts_text_with_page_and_coordinates(tmp_path: Path) -> None:
    path = tmp_path / "invoice.pdf"
    with pymupdf.open() as pdf:
        first = pdf.new_page()
        first.insert_text((72, 72), "Invoice number: INV-123")
        second = pdf.new_page()
        second.insert_text((72, 72), "Total: 119.00 EUR")
        pdf.save(path)

    result = ingest_pdf(path)

    assert result.filename == "invoice.pdf"
    assert len(result.pages) == 2
    assert "INV-123" in result.pages[0].blocks[0].text
    assert "119.00" in result.pages[1].blocks[0].text
    assert result.pages[0].blocks[0].id.startswith("p1-b")
    assert result.pages[1].blocks[0].page == 2
    x0, y0, x1, y1 = result.pages[0].blocks[0].bbox
    assert x0 < x1 and y0 < y1
    assert not result.pages[0].needs_ocr


def test_flags_image_only_page_for_ocr(tmp_path: Path) -> None:
    path = tmp_path / "scanned.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        pixmap = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), False)
        pixmap.clear_with(255)
        page.insert_image(pymupdf.Rect(20, 20, 100, 100), pixmap=pixmap)
        pdf.save(path)

    result = ingest_pdf(path)

    assert result.pages[0].blocks == []
    assert result.pages[0].needs_ocr


def test_blank_page_is_not_mistaken_for_scan(tmp_path: Path) -> None:
    path = tmp_path / "blank.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(path)

    assert not ingest_pdf(path).pages[0].needs_ocr


def test_rejects_invalid_pdf(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not actually a PDF")

    with pytest.raises(DocumentIngestionError, match="Invalid or damaged"):
        ingest_pdf(path)


def test_rejects_non_pdf_input(tmp_path: Path) -> None:
    with pytest.raises(DocumentIngestionError, match="Only PDF"):
        ingest_pdf(tmp_path / "image.png")
