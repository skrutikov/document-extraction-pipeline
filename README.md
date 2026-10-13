# Document Extraction Pipeline

An incremental demonstration of **document ingestion, source traceability,
and (in later stages) AI-powered field extraction and deterministic validation**.

## Milestone 2: OCR fallback for scanned PDFs

The pipeline first extracts digital text blocks with **PyMuPDF**. For pages
containing raster images and fewer than 20 non-whitespace characters of digital
text (for example, only a stray bullet), it can optionally use
**Tesseract OCR** via PyMuPDF's built-in integration.

Both paths return the same Pydantic models, with one-based page numbers,
bounding boxes in PDF points, and a `source` field (`pdf_text` or `ocr`).
If OCR is disabled or cannot recognize text on a page needing OCR,
`needs_ocr` remains `true`.

See the [architecture diagram](docs/architecture.md) for the full flow and
current limitations.

### Install

Requires Python 3.11+ and, for OCR, the **Tesseract executable and language data**.
Tesseract is a system dependency, not a pip package.

Ubuntu/Debian:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
```

macOS (Homebrew):

```bash
brew install tesseract tesseract-lang
```

Check installed languages with `tesseract --list-langs`. The default is English;
use `--language deu+eng` for German and English receipts.

Create a virtual environment and install the Python project:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Try it

For a digital PDF:

```bash
python -m document_extraction_pipeline path/to/invoice.pdf
```

For a scanned PDF:

```bash
python -m document_extraction_pipeline path/to/scanned-invoice.pdf --ocr --language deu+eng
```

Run tests:

```bash
python -m pytest -v
```

A sample text block looks like this (coordinates are illustrative):

```json
{
  "id": "p1-b0",
  "page": 1,
  "bbox": [72.0, 60.0, 220.0, 76.0],
  "text": "Total: 119.00 EUR",
  "source": "ocr"
}
```

**Limitations:** OCR is currently used only on image-containing pages with fewer than 20
non-whitespace native text characters. Mixed pages with substantial digital
text, reading order, table understanding, confidence scores, LLM
field extraction, and evidence validation are future work.

## Next milestones

1. Structured LLM extraction (e.g. supplier, total, currency).
2. Source-based verification and arithmetic/business-rule validation.
3. API, reproducible fixtures, and evaluation metrics.

**Privacy:** Do not commit personal receipts, customer documents, or API keys.
Local documents should remain in `data/` or `samples/private/`, which are ignored.
