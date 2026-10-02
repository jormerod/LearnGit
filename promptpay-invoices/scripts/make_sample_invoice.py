#!/usr/bin/env python3
"""Create a minimal invoice PDF for local smoke tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pymupdf


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "sample-invoice.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 72), "Condo Invoice", fontsize=16)
    page.insert_text((72, 110), "Condo No: 6908")
    page.insert_text((72, 130), "Invoice No: 6909000127")
    page.insert_text((72, 150), "Unit: A430")
    page.insert_text((72, 180), "Total Amount: 1,250.00")
    page.insert_text((72, 220), "(QR will be placed top-right on processing)")
    doc.save(out)
    doc.close()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
