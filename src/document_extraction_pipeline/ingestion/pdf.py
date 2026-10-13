"""Digital-PDF text extraction with page and bounding-box provenance.

This is deliberately not OCR. Image-only pages are flagged for a future OCR stage.
"""

from pathlib import Path

import pymupdf

from document_extraction_pipeline.models import IngestedDocument, PageContent, TextBlock

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PAGES = 100


class DocumentIngestionError(ValueError):
    """The document cannot safely be ingested."""


def ingest_pdf(path: str | Path) -> IngestedDocument:
    """Extract text blocks from a PDF without losing their source locations.

    Block IDs are page-local PDF block numbers, suitable for references within
    this ingestion. No OCR, layout reconstruction, or table understanding yet.
    """
    source = Path(path)
    if source.suffix.lower() != ".pdf":
        raise DocumentIngestionError("Only PDF files are supported")
    if not source.is_file():
        raise DocumentIngestionError(f"PDF not found: {source}")
    if source.stat().st_size > MAX_FILE_BYTES:
        raise DocumentIngestionError("PDF exceeds the 20 MiB size limit")

    try:
        with pymupdf.open(source) as pdf:
            if pdf.needs_pass:
                raise DocumentIngestionError("Password-protected PDFs are not supported")
            if len(pdf) > MAX_PAGES:
                raise DocumentIngestionError("PDF exceeds the 100-page limit")

            pages: list[PageContent] = []
            for number, page in enumerate(pdf, start=1):
                blocks: list[TextBlock] = []
                # Each text tuple is (x0,y0,x1,y1,text,block_no,block_type).
                for item in page.get_text("blocks", sort=True):
                    x0, y0, x1, y1, text, block_number, block_type = item[:7]
                    if block_type != 0 or not text.strip():
                        continue
                    blocks.append(
                        TextBlock(
                            id=f"p{number}-b{block_number}",
                            page=number,
                            bbox=(x0, y0, x1, y1),
                            text=text.strip(),
                        )
                    )
                # A truly blank page should not be mistaken for a failed OCR page.
                needs_ocr = not blocks and bool(page.get_images(full=True))
                pages.append(PageContent(number=number, blocks=blocks, needs_ocr=needs_ocr))
    except (pymupdf.FileDataError, pymupdf.EmptyFileError) as exc:
        raise DocumentIngestionError("Invalid or damaged PDF") from exc

    return IngestedDocument(filename=source.name, pages=pages)
