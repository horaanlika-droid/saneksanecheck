"""Общие хелперы бота: проверка админа, безопасное редактирование, файлы."""

from __future__ import annotations

import functools
from datetime import datetime
from pathlib import Path

from aiogram.types import CallbackQuery, Message

from app import db
from app.config import get_settings
from app.images import delete_files


def admin_only(func):
    """Декоратор: пускает только администраторов."""

    @functools.wraps(func)
    async def wrapper(event: Message | CallbackQuery, *args, **kwargs):
        user = event.from_user
        if not user or not await db.is_admin(user.id):
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Только для администратора", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("⛔ Эта команда только для администратора.")
            return None
        return await func(event, *args, **kwargs)

    return wrapper


async def safe_edit(message: Message, text: str, reply_markup=None) -> Message:
    """Редактирует сообщение, при неудаче шлёт новое."""
    try:
        return await message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        return await message.answer(text, reply_markup=reply_markup)


def fmt_dt(ts: int) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return ""


async def webapp_url() -> str:
    return get_settings().WEBAPP_URL or await db.get_setting("webapp_url", "")


async def delete_upload_files(paths: list[str]) -> None:
    """Удаляет файлы с диска, если на них больше никто не ссылается."""
    upload_dir = get_settings().upload_dir
    for p in paths:
        if not p:
            continue
        name = Path(p).name
        refs = await db.path_refs_count(name)
        if refs <= 0:
            delete_files(upload_dir, [name])


def short(text: str, n: int = 40) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= n else text[: n - 1] + "…"
