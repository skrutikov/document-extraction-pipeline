"""OCR integration tests use generated images, never personal receipts."""

from pathlib import Path
import shutil

import pymupdf
import pytest

from document_extraction_pipeline.ingestion.pdf import ingest_pdf


def make_scanned_pdf(path: Path) -> None:
    # Rasterize a temporary text page, then embed its pixels in a new PDF.
    with pymupdf.open() as digital:
        page = digital.new_page()
        page.insert_text((72, 120), "INVOICE INV-123", fontsize=24)
        page.insert_text((72, 170), "TOTAL 119.00 EUR", fontsize=24)
        image = page.get_pixmap(matrix=pymupdf.Matrix(2, 2)).tobytes("png")

    with pymupdf.open() as scanned:
        page = scanned.new_page()
        page.insert_image(page.rect, stream=image)
        scanned.save(path)


def make_scanned_pdf_with_stray_bullet(path: Path) -> None:
    # A Word-export-like PDF: full-page scanned content plus a stray bullet.
    make_scanned_pdf(path)
    with pymupdf.open(path) as pdf:
        pdf[0].insert_text((72, 72), "•", fontname="helv")
        pdf.saveIncr()


def test_short_native_text_on_scanned_page_needs_ocr(tmp_path: Path) -> None:
    path = tmp_path / "scan-with-bullet.pdf"
    make_scanned_pdf_with_stray_bullet(path)
    result = ingest_pdf(path)
    page = result.pages[0]
    assert page.needs_ocr
    assert len(page.blocks) == 1
    # Helvetica may map the input bullet to a middle dot in extracted PDF text.
    assert len(page.blocks[0].text.strip()) == 1
    assert page.blocks[0].source == "pdf_text"


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract not installed")
def test_ocr_replaces_stray_bullet_with_scanned_text(tmp_path: Path) -> None:
    path = tmp_path / "scan-with-bullet.pdf"
    make_scanned_pdf_with_stray_bullet(path)
    page = ingest_pdf(path, ocr=True).pages[0]
    assert not page.needs_ocr
    assert page.blocks
    assert all(block.source == "ocr" for block in page.blocks)
    assert "INV-123" in " ".join(block.text for block in page.blocks)


def test_ocr_is_opt_in(tmp_path: Path) -> None:
    path = tmp_path / "scan.pdf"
    make_scanned_pdf(path)
    result = ingest_pdf(path)
    assert result.pages[0].needs_ocr
    assert result.pages[0].blocks == []


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract not installed")
def test_ocr_recognizes_scanned_invoice_with_coordinates(tmp_path: Path) -> None:
    path = tmp_path / "scan.pdf"
    make_scanned_pdf(path)
    result = ingest_pdf(path, ocr=True)
    page = result.pages[0]
    assert not page.needs_ocr
    assert page.blocks
    assert all(block.source == "ocr" for block in page.blocks)
    text = " ".join(block.text for block in page.blocks)
    assert "INV-123" in text
    assert "119.00" in text
    for block in page.blocks:
        x0, y0, x1, y1 = block.bbox
        assert 0 <= x0 < x1 <= 595.1
        assert 0 <= y0 < y1 <= 842.1


def test_digital_pdf_does_not_need_ocr(tmp_path: Path) -> None:
    path = tmp_path / "digital.pdf"
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "Invoice 123")
        pdf.save(path)
    result = ingest_pdf(path, ocr=True)
    assert result.pages[0].blocks[0].source == "pdf_text"
    assert not result.pages[0].needs_ocr


def test_blank_page_stays_blank_with_ocr(tmp_path: Path) -> None:
    path = tmp_path / "blank.pdf"
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(path)
    result = ingest_pdf(path, ocr=True)
    assert result.pages[0].blocks == []
    assert not result.pages[0].needs_ocr
