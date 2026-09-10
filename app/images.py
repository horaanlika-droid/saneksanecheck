"""Обработка изображений: ресайз, конвертация в JPEG, превью."""

from __future__ import annotations

import io
import uuid
from pathlib import Path

from PIL import Image, ImageOps


def process_image_bytes(
    data: bytes,
    upload_dir: Path,
    max_size: int = 2048,
    thumb_size: int = 900,
    quality: int = 85,
) -> dict:
    """Сохраняет фото + превью на диск. Возвращает имена файлов и размеры."""
    upload_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    w, h = img.size
    scale = min(1.0, max_size / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    stem = uuid.uuid4().hex[:12]
    fname = f"{stem}.jpg"
    tname = f"{stem}_t.jpg"
    img.save(upload_dir / fname, "JPEG", quality=quality, optimize=True, progressive=True)

    tw, th = img.size
    tscale = min(1.0, thumb_size / max(tw, th))
    thumb = img.resize((int(tw * tscale), int(th * tscale)), Image.LANCZOS) if tscale < 1.0 else img
    thumb.save(upload_dir / tname, "JPEG", quality=80, optimize=True, progressive=True)

    return {"file": fname, "thumb": tname, "w": img.size[0], "h": img.size[1]}


def delete_files(upload_dir: Path, paths: list[str]) -> None:
    for p in paths:
        if not p:
            continue
        try:
            f = upload_dir / Path(p).name
            if f.exists():
                f.unlink()
        except OSError:
            pass
