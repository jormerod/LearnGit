from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

FILENAME_PATTERN = re.compile(
    r"^(?P<condo>\d+)-(?P<invoice>\d+)-(?P<unit>[A-Za-z0-9]+)",
    re.IGNORECASE,
)

INVOICE_PATTERNS = [
    re.compile(r"invoice\s*(?:no\.?|#|number)?\s*[:\s]*([0-9-]+)", re.I),
    re.compile(r"เลขที่ใบแจ้งหนี้\s*[:.]?\s*([0-9-]+)"),
    re.compile(r"ใบแจ้งหนี้\s*(?:เลขที่)?\s*[:.]?\s*([0-9-]+)"),
]

CONDO_PATTERNS = [
    re.compile(r"condo\s*(?:no\.?|#)?\s*[:\s]*(\d+)", re.I),
    re.compile(r"building\s*(?:no\.?|#)?\s*[:\s]*(\d+)", re.I),
    re.compile(r"โครงการ\s*(\d+)"),
]

AMOUNT_PATTERNS = [
    re.compile(r"total\s*(?:amount|due)?\s*[:\s]*(?:THB|฿)?\s*([0-9,]+\.?\d*)", re.I),
    re.compile(r"amount\s*due\s*[:\s]*([0-9,]+\.?\d*)", re.I),
    re.compile(r"ยอดชำระ\s*([0-9,]+\.?\d*)"),
    re.compile(r"รวม(?:ทั้งสิ้น)?\s*([0-9,]+\.?\d*)"),
]


@dataclass
class InvoiceFields:
    condo: str | None
    invoice: str | None
    unit: str | None
    amount: float | None
    text_sample: str

    def as_dict(self) -> dict:
        return {
            "condo": self.condo,
            "invoice": self.invoice,
            "unit": self.unit,
            "amount": self.amount,
        }


def _first_match(patterns: list[re.Pattern[str]], text: str) -> str | None:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return None


def _parse_amount(raw: str | None) -> float | None:
    if not raw:
        return None
    cleaned = raw.replace(",", "").strip()
    try:
        value = float(cleaned)
        return value if value > 0 else None
    except ValueError:
        return None


def extract_text_from_pdf(path: Path) -> str:
    chunks: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages[:3]:
            chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def extract_fields(path: Path) -> InvoiceFields:
    text = extract_text_from_pdf(path)
    stem = path.stem

    condo = _first_match(CONDO_PATTERNS, text)
    invoice = _first_match(INVOICE_PATTERNS, text)
    amount = _parse_amount(_first_match(AMOUNT_PATTERNS, text))
    unit: str | None = None

    fn = FILENAME_PATTERN.match(stem)
    if fn:
        condo = condo or fn.group("condo")
        invoice = invoice or fn.group("invoice")
        unit = fn.group("unit")

    return InvoiceFields(
        condo=condo,
        invoice=invoice,
        unit=unit,
        amount=amount,
        text_sample=text[:500],
    )
