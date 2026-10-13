"""Inspect PDF text as JSON: python -m document_extraction_pipeline file.pdf --ocr"""

import argparse

from document_extraction_pipeline.ingestion.pdf import DocumentIngestionError, ingest_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract PDF text with source locations")
    parser.add_argument("pdf", help="Path to a PDF")
    parser.add_argument("--ocr", action="store_true", help="OCR image-only pages with Tesseract")
    parser.add_argument("--language", default="eng", help="Tesseract languages, e.g. eng or deu+eng")
    args = parser.parse_args()
    try:
        print(ingest_pdf(args.pdf, ocr=args.ocr, language=args.language).model_dump_json(indent=2))
    except DocumentIngestionError as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
