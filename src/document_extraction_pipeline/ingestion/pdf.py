"""PDF ingestion with optional OCR fallback and source coordinates.

Digital text is preferred. When a page has no extractable text but contains
raster images, optional Tesseract OCR recovers text from a rendered page.
"""

from pathlib import Path

import pymupdf

from document_extraction_pipeline.models import IngestedDocument, PageContent, TextBlock

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PAGES = 100
OCR_DPI = 200
MAX_OCR_PIXELS = 25_000_000


class DocumentIngestionError(ValueError):
    """The document cannot safely be ingested."""


def _extract_blocks(page: pymupdf.Page, number: int, *, textpage: pymupdf.TextPage | None = None, source: str = "pdf_text") -> list[TextBlock]:
    blocks: list[TextBlock] = []
    # Each tuple: (x0, y0, x1, y1, text, block_no, block_type).
    for item in page.get_text("blocks", sort=True, textpage=textpage):
        x0, y0, x1, y1, text, block_number, block_type = item[:7]
        if block_type != 0 or not text.strip():
            continue
        blocks.append(
            TextBlock(
                id=f"p{number}-b{block_number}",
                page=number,
                bbox=(x0, y0, x1, y1),
                text=text.strip(),
                source=source,
            )
        )
    return blocks


def ingest_pdf(path: str | Path, *, ocr: bool = False, language: str = "eng") -> IngestedDocument:
    """Extract digital text and optionally OCR image-only pages.

    Coordinates are PDF points (not OCR pixels). OCR needs a system installation
    of Tesseract with the requested language data. Image regions on pages that
    already have digital text are not OCRed in this initial fallback strategy.
    """
    source = Path(path)
    if source.suffix.lower() != ".pdf":
        raise DocumentIngestionError("Only PDF files are supported")
    if not source.is_file():
        raise DocumentIngestionError(f"PDF not found: {source}")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise DocumentIngestionError("PDF exceeds the 20 MiB size limit")
    if not language or not all(c.isalnum() or c in "+_" for c in language):
        raise DocumentIngestionError("Invalid OCR language identifier")

    try:
        with pymupdf.open(source) as pdf:
            if pdf.needs_pass:
                raise DocumentIngestionError("Password-protected PDFs are not supported")
            if len(pdf) > MAX_PAGES:
                raise DocumentIngestionError("PDF exceeds the 100-page limit")

            pages: list[PageContent] = []
            for number, page in enumerate(pdf, start=1):
                blocks = _extract_blocks(page, number)
                has_images = bool(page.get_images(full=True))
                needs_ocr = not blocks and has_images
                if needs_ocr and ocr:
                    width_px = page.rect.width * OCR_DPI / 72
                    height_px = page.rect.height * OCR_DPI / 72
                    if width_px * height_px > MAX_OCR_PIXELS:
                        raise DocumentIngestionError(f"Page {number} is too large for OCR")
                    try:
                        textpage = page.get_textpage_ocr(language=language, dpi=OCR_DPI, full=True)
                    except Exception as exc:
                        raise DocumentIngestionError(
                            f"OCR failed on page {number}. Install Tesseract and the '{language}' language data."
                        ) from exc
                    blocks = _extract_blocks(page, number, textpage=textpage, source="ocr")
                    needs_ocr = not blocks
                pages.append(PageContent(number=number, blocks=blocks, needs_ocr=needs_ocr))
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise DocumentIngestionError("Invalid or damaged PDF") from exc

    return IngestedDocument(filename=source.name, pages=pages)
