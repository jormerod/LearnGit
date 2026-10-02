# Batch PromptPay Invoice QR (MVP)

Minimal web app: upload invoice PDFs in batch, extract invoice/condo identifiers, generate PromptPay QR codes, stamp them on page 1, download individually or as ZIP.

## Requirements

- Python 3.10+
- PromptPay merchant **ID** (phone or tax ID) from your organization

## Setup

```bash
cd promptpay-invoices
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PROMPTPAY_DATA_DIR="$(pwd)/data"
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Open http://localhost:8080

## Configuration

| Variable | Description |
|----------|-------------|
| `PROMPTPAY_DATA_DIR` | Batch storage root (default: `data`) |
| `PROMPTPAY_MAX_FILES` | Max PDFs per batch (default: 1000) |
| `PROMPTPAY_QR_RECT` | Optional `x,y,width,height` in PDF points for QR placement |

## Extraction

1. PDF text via pdfplumber (invoice / condo / amount regexes).
2. Filename fallback: `{condo}-{invoice}-{unit}_*.pdf` (e.g. `6908-6909000127-A430_108b.pdf`).

## PromptPay library

Uses [promptpay-qr](https://pypi.org/project/promptpay-qr/) (MIT, EMV QRCPS Merchant Presented Mode).

## Smoke test (synthetic PDF)

```bash
python scripts/make_sample_invoice.py /tmp/demo-invoice.pdf
curl -F "promptpay_id=0812345678" -F "default_amount=99.50" \
  -F "files=@/tmp/demo-invoice.pdf" http://127.0.0.1:8080/api/batches
```

## Not in MVP

- OCR for scanned invoices
- Bill payment (Biller ID + Ref1) QR — use `promptparse-py` when required
- Authentication / cloud storage
