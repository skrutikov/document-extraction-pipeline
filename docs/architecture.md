# Architecture (incremental)

The ingestion stage works without an LLM and preserves page-level evidence.

```mermaid
flowchart TD
    A[PDF] --> B[Validate file size and page count]
    B --> C[PyMuPDF digital text extraction]
    C --> D{At least 20 text chars?}
    D -->|Yes| E[Native text blocks]
    D -->|No, image present| F{OCR enabled?}
    D -->|No, no image| G[Keep native text or empty page]
    F -->|Yes| H[Tesseract OCR via PyMuPDF]
    F -->|No| I[needs_ocr = true]
    H --> J[OCR text blocks]
    E --> K[JSON document model]
    G --> K
    I --> K
    J --> K
    K -. Future .-> L[LLM structured extraction]
    L -. Future .-> M[Evidence and business-rule validation]
```

Both digital and OCR text blocks carry one-based page numbers, PDF-point
bounding boxes, and a `source` field (`pdf_text` or `ocr`).
Block IDs refer to a single ingestion, not a stable cross-version identifier.

## Current limitations

- OCR is opt-in (`--ocr`) and needs a separate Tesseract installation.
- OCR fallback is applied only to image-containing pages with **fewer than 20
  non-whitespace native text characters** (e.g., stray bullets). Pages with
  substantial digital text and additional scanned content are not fully covered.
- Text blocks are not a guarantee of correct reading order or table structure.
- No OCR confidence scores, document field extraction, validation, or RAG yet.
- `needs_ocr` remains true when OCR is disabled or yields no text on a page
  that meets the fallback criteria. Existing short native text is retained if
  OCR yields nothing.
