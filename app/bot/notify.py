"""Общий доступ к экземпляру бота из веб-сервера (уведомления, медиа-фолбэк)."""

from __future__ import annotations

import logging
from datetime import datetime

from aiogram import Bot

log = logging.getLogger(__name__)

_bot: Bot | None = None


def set_bot(bot: Bot | None) -> None:
    global _bot
    _bot = bot


def get_bot() -> Bot | None:
    return _bot


async def notify_admins(text: str, reply_markup=None) -> None:
    from app import db
    bot = get_bot()
    if bot is None:
        return
    for admin_id in await db.list_admin_ids():
        try:
            await bot.send_message(admin_id, text, reply_markup=reply_markup)
        except Exception as e:
            log.warning("notify %s failed: %s", admin_id, e)


async def notify_new_lead(lead_id: int) -> None:
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from app import db

    lead = await db.get_lead(lead_id)
    if not lead:
        return
    dt = datetime.fromtimestamp(lead["created_at"]).strftime("%d.%m %H:%M")
    text = (
        "🔔 <b>Новая заявка!</b>\n\n"
        f"👤 {lead['name']}\n"
        f"📞 {lead['contact']}\n"
    )
    if lead["service_title"]:
        text += f"💼 {lead['service_title']}\n"
    if lead["date_text"]:
        text += f"📅 {lead['date_text']}\n"
    if lead["message"]:
        text += f"💬 {lead['message']}\n"
    text += f"\n🕐 {dt}  ·  #{lead['id']}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Принять", callback_data=f"lead:ok:{lead['id']}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"lead:no:{lead['id']}"),
    ]])
    await notify_admins(text, kb)
