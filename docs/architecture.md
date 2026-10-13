# Architecture (incremental)

The ingestion stage works without an LLM and preserves page-level evidence.

```mermaid
flowchart TD
    A[PDF] --> B[Check file size and page count]
    B --> C[PyMuPDF text extraction]
    C --> D{Extracted text?}
    D -->|Yes| E[Text blocks with page and bounding box]
    D -->|No and raster images| F[Flag needs_ocr]
    D -->|No and no images| G[Empty page]
    E --> H[JSON document model]
    F --> H
    G --> H
    H -. Future .-> I[OCR fallback]
    H -. Future .-> J[LLM structured extraction]
    J -. Future .-> K[Evidence and arithmetic validation]
```

This first milestone **does not** perform OCR, reconstruct tables or reading order,
verify extracted facts, or use RAG. Text blocks preserve positions in PDF points;
source-block IDs refer to a single ingestion, not a stable cross-version identifier.

Planned next step: add OCR for scanned pages, preserving word-level evidence.
