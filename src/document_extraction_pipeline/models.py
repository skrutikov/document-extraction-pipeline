"""Typed representations of document content and its source locations."""

from typing import Literal

from pydantic import BaseModel, Field


class TextBlock(BaseModel):
    """Text taken from one PDF page, with source coordinates in PDF points."""

    id: str = Field(description="Stable within one ingestion, e.g. p1-b0")
    page: int = Field(ge=1, description="One-based PDF page number")
    bbox: tuple[float, float, float, float] = Field(
        description="Coordinates (x0, y0, x1, y1) in PDF points"
    )
    text: str
    source: Literal["pdf_text", "ocr"] = Field(
        default="pdf_text", description="Whether text was native or recognized by OCR"
    )


class PageContent(BaseModel):
    number: int = Field(ge=1)
    blocks: list[TextBlock]
    needs_ocr: bool = Field(
        description="True if an image-only page still has no recognized text"
    )


class IngestedDocument(BaseModel):
    filename: str
    pages: list[PageContent]
