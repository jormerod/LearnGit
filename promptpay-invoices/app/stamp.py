from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from promptpay_qr import generate_qr_image

from app.config import settings


def default_qr_rect(page: pymupdf.Page, qr_size: float = 120.0) -> pymupdf.Rect:
    margin = 36.0
    x1 = page.rect.width - margin - qr_size
    y1 = margin
    return pymupdf.Rect(x1, y1, x1 + qr_size, y1 + qr_size)


def qr_rect_for_page(page: pymupdf.Page) -> pymupdf.Rect:
    if settings.qr_rect:
        x, y, w, h = settings.qr_rect
        return pymupdf.Rect(x, y, x + w, y + h)
    return default_qr_rect(page)


def stamp_promptpay_qr(
    source_pdf: Path,
    dest_pdf: Path,
    promptpay_id: str,
    amount: float | None,
) -> None:
    img = generate_qr_image(promptpay_id, amount=amount, size=400)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    doc = pymupdf.open(source_pdf)
    try:
        page = doc[0]
        rect = qr_rect_for_page(page)
        page.insert_image(rect, stream=png_bytes, keep_proportion=True)
        dest_pdf.parent.mkdir(parents=True, exist_ok=True)
        doc.save(dest_pdf, garbage=4, deflate=True)
    finally:
        doc.close()
