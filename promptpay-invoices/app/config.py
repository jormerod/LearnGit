from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    max_files_per_batch: int
    qr_rect: tuple[float, float, float, float] | None

    @classmethod
    def from_env(cls) -> Settings:
        base = Path(os.environ.get("PROMPTPAY_DATA_DIR", "data"))
        rect_env = os.environ.get("PROMPTPAY_QR_RECT", "").strip()
        qr_rect: tuple[float, float, float, float] | None = None
        if rect_env:
            parts = [float(p.strip()) for p in rect_env.split(",")]
            if len(parts) == 4:
                qr_rect = (parts[0], parts[1], parts[2], parts[3])
        return cls(
            data_dir=base,
            max_files_per_batch=int(os.environ.get("PROMPTPAY_MAX_FILES", "1000")),
            qr_rect=qr_rect,
        )


settings = Settings.from_env()
