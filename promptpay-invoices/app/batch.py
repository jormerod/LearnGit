from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.extract import extract_fields
from app.stamp import stamp_promptpay_qr


@dataclass
class FileResult:
    filename: str
    condo: str | None = None
    invoice: str | None = None
    unit: str | None = None
    amount: float | None = None
    status: str = "pending"
    error: str | None = None
    output_name: str | None = None


@dataclass
class BatchJob:
    batch_id: str
    created_at: str
    promptpay_id: str
    default_amount: float | None
    files: list[FileResult] = field(default_factory=list)

    def to_manifest(self) -> dict:
        return {
            "batch_id": self.batch_id,
            "created_at": self.created_at,
            "promptpay_id": self.promptpay_id,
            "default_amount": self.default_amount,
            "files": [asdict(f) for f in self.files],
        }


def batch_dir(batch_id: str) -> Path:
    return settings.data_dir / "batches" / batch_id


def process_batch(
    uploaded_paths: list[tuple[str, Path]],
    promptpay_id: str,
    default_amount: float | None = None,
) -> BatchJob:
    batch_id = str(uuid.uuid4())
    root = batch_dir(batch_id)
    incoming = root / "incoming"
    outgoing = root / "outgoing"
    incoming.mkdir(parents=True, exist_ok=True)
    outgoing.mkdir(parents=True, exist_ok=True)

    job = BatchJob(
        batch_id=batch_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        promptpay_id=promptpay_id,
        default_amount=default_amount,
    )

    for original_name, tmp_path in uploaded_paths:
        safe_name = Path(original_name).name
        dest_in = incoming / safe_name
        shutil.copy2(tmp_path, dest_in)

        result = FileResult(filename=safe_name)
        job.files.append(result)

        try:
            fields = extract_fields(dest_in)
            result.condo = fields.condo
            result.invoice = fields.invoice
            result.unit = fields.unit
            result.amount = fields.amount or default_amount

            if not result.invoice and not result.condo:
                raise ValueError(
                    "Could not extract invoice or condo number; check filename or PDF text"
                )

            out_name = f"promptpay_{safe_name}"
            dest_out = outgoing / out_name
            stamp_promptpay_qr(
                dest_in,
                dest_out,
                promptpay_id=promptpay_id,
                amount=result.amount,
            )
            result.output_name = out_name
            result.status = "ok"
        except Exception as exc:  # noqa: BLE001 — surface per-file errors in manifest
            result.status = "error"
            result.error = str(exc)

    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(job.to_manifest(), indent=2), encoding="utf-8")
    return job


def load_manifest(batch_id: str) -> dict | None:
    path = batch_dir(batch_id) / "manifest.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_zip(batch_id: str, dest_zip: Path) -> None:
    outgoing = batch_dir(batch_id) / "outgoing"
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for pdf in sorted(outgoing.glob("*.pdf")):
            zf.write(pdf, arcname=pdf.name)
        manifest = batch_dir(batch_id) / "manifest.json"
        if manifest.is_file():
            zf.write(manifest, arcname="manifest.json")
