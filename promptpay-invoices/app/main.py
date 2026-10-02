from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.batch import batch_dir, build_zip, load_manifest, process_batch
from app.config import settings

app = FastAPI(title="Batch PromptPay Invoice QR")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "max_files": settings.max_files_per_batch},
    )


@app.post("/api/batches")
async def create_batch(
    promptpay_id: str = Form(...),
    default_amount: str | None = Form(None),
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > settings.max_files_per_batch:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.max_files_per_batch} files per batch",
        )

    amount_val: float | None = None
    if default_amount and default_amount.strip():
        try:
            amount_val = float(default_amount.replace(",", ""))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid default_amount") from exc

    uploaded: list[tuple[str, Path]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for uf in files:
            if not uf.filename or not uf.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"Not a PDF: {uf.filename}")
            dest = tmp_path / Path(uf.filename).name
            content = await uf.read()
            dest.write_bytes(content)
            uploaded.append((uf.filename, dest))

        # Copy paths out of temp before process_batch reads them
        persisted: list[tuple[str, Path]] = []
        staging = tmp_path / "staging"
        staging.mkdir()
        for name, src in uploaded:
            copy = staging / Path(name).name
            copy.write_bytes(src.read_bytes())
            persisted.append((name, copy))

        job = process_batch(persisted, promptpay_id=promptpay_id.strip(), default_amount=amount_val)

    return job.to_manifest()


@app.get("/api/batches/{batch_id}")
async def get_batch(batch_id: str):
    manifest = load_manifest(batch_id)
    if not manifest:
        raise HTTPException(status_code=404, detail="Batch not found")
    return manifest


@app.get("/api/batches/{batch_id}/files/{output_name}")
async def download_file(batch_id: str, output_name: str):
    safe = Path(output_name).name
    path = batch_dir(batch_id) / "outgoing" / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename=safe)


@app.get("/api/batches/{batch_id}/download.zip")
async def download_zip(batch_id: str):
    root = batch_dir(batch_id)
    if not root.is_dir():
        raise HTTPException(status_code=404, detail="Batch not found")
    zip_path = root / "batch.zip"
    build_zip(batch_id, zip_path)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"promptpay-batch-{batch_id[:8]}.zip",
    )
