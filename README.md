# Document Extraction Pipeline

A small, incremental demonstration of **document ingestion, source traceability,
and (in later stages) AI-powered field extraction and deterministic validation**.

## Milestone 1: Text-based PDF ingestion

The current implementation extracts text blocks from **digital PDFs** using
PyMuPDF. Each block includes a one-based page number and its bounding box in
PDF coordinates. Image-only pages are flagged with `needs_ocr: true` rather
than silently treated as successfully parsed documents.

It **does not yet** OCR scans, interpret tables, extract invoice fields with an
LLM, or validate extracted values. See [architecture](docs/architecture.md).

### Install

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e '.[dev]'
```

### Try it

```bash
python -m document_extraction_pipeline path/to/invoice.pdf
pytest
```

The CLI emits JSON, including text blocks and their source locations:

```json
{
  "filename": "invoice.pdf",
  "pages": [
    {
      "number": 1,
      "blocks": [
        {"id": "p1-b0", "page": 1, "bbox": [72.0, 60.0, 220.0, 76.0], "text": "Invoice: INV-123"}
      ],
      "needs_ocr": false
    }
  ]
}
```

The example above is illustrative; actual bounding boxes depend on the PDF.

## Next milestones

1. OCR fallback for scanned or mixed-content documents.
2. Structured LLM extraction (e.g. supplier, total, and currency).
3. Source-based verification, validation, and meaningful error handling.
4. API, reproducible sample fixtures, and evaluation metrics.

**Privacy:** Do not commit personal receipts, customer documents, or API keys.
Local documents should remain in `data/` or `samples/private/`, which are ignored.
