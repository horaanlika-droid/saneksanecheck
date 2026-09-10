"""Работа с фотографиями из Telegram: скачивание, обработка, копии."""

from __future__ import annotations

import io
import shutil
import uuid

from aiogram import Bot
from aiogram.types import Message

from app.config import get_settings
from app.images import process_image_bytes


async def save_tg_photo(bot: Bot, message: Message) -> dict | None:
    """Скачивает самое большое фото из сообщения, обрабатывает и сохраняет.
    Возвращает dict(file, thumb, w, h, file_id) или None."""
    if not message.photo:
        return None
    biggest = message.photo[-1]
    buf = io.BytesIO()
    await bot.download(biggest.file_id, destination=buf)
    data = buf.getvalue()
    if not data:
        return None
    info = process_image_bytes(data, get_settings().upload_dir)
    info["file_id"] = biggest.file_id
    return info


def copy_upload(name: str) -> str:
    """Делает независимую копию файла в uploads, возвращает новое имя."""
    upload_dir = get_settings().upload_dir
    src = upload_dir / name
    if not name or not src.exists():
        return ""
    new_name = f"{uuid.uuid4().hex[:12]}.jpg"
    shutil.copy(src, upload_dir / new_name)
    return new_name
