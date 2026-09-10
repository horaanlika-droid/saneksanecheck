"""Заявки из формы записи на сайте."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, fmt_dt, safe_edit

router = Router()


def lead_text(lead: dict) -> str:
    st = kb.LEAD_STATUS.get(lead["status"], lead["status"])
    text = (
        f"{st} · заявка #{lead['id']}\n\n"
        f"👤 {lead['name']}\n"
        f"📞 {lead['contact']}\n"
    )
    if lead["service_title"]:
        text += f"💼 {lead['service_title']}\n"
    if lead["date_text"]:
        text += f"📅 {lead['date_text']}\n"
    if lead["message"]:
        text += f"💬 {lead['message']}\n"
    text += f"\n🕐 {fmt_dt(lead['created_at'])}"
    return text


async def show_list(message: Message, show_all: bool = False) -> None:
    leads = await db.list_leads(None if show_all else "new", 20)
    title = "📋 <b>Все заявки</b>" if show_all else "💬 <b>Новые заявки</b>"
    if not leads:
        text = title + "\n\nПока пусто ✨"
    else:
        text = title + f"\n\nПоказано: {len(leads)}"
    await safe_edit(message, text, kb.leads_list(leads, show_all))


@router.message(Command("leads"))
@admin_only
async def cmd_leads(message: Message):
    leads = await db.list_leads("new", 20)
    if not leads:
        await message.answer("💬 Новых заявок нет ✨")
        return
    await message.answer(f"💬 <b>Новые заявки</b>\n\nПоказано: {len(leads)}", reply_markup=kb.leads_list(leads, False))


@router.callback_query(F.data == "leads")
@admin_only
async def cb_leads(call: CallbackQuery):
    await call.answer()
    await show_list(call.message, False)  # type: ignore


@router.callback_query(F.data == "leads:all")
@admin_only
async def cb_leads_all(call: CallbackQuery):
    await call.answer()
    await show_list(call.message, True)  # type: ignore


@router.callback_query(F.data.startswith("lead:view:"))
@admin_only
async def cb_view(call: CallbackQuery):
    lead = await db.get_lead(int(call.data.split(":")[2]))  # type: ignore
    await call.answer()
    if not lead:
        await safe_edit(call.message, "Заявка не найдена.", kb.back_to("leads").as_markup())  # type: ignore
        return
    await safe_edit(call.message, lead_text(lead), kb.lead_card(lead["id"]))  # type: ignore


async def _set_status(call: CallbackQuery, status: str, toast: str) -> None:
    lead_id = int(call.data.split(":")[2])  # type: ignore
    await db.set_lead_status(lead_id, status)
    await call.answer(toast)
    lead = await db.get_lead(lead_id)
    if lead:
        await safe_edit(call.message, lead_text(lead), kb.lead_card(lead_id))  # type: ignore


@router.callback_query(F.data.startswith("lead:ok:"))
@admin_only
async def cb_ok(call: CallbackQuery):
    await _set_status(call, "accepted", "✅ Заявка принята")


@router.callback_query(F.data.startswith("lead:no:"))
@admin_only
async def cb_no(call: CallbackQuery):
    await _set_status(call, "declined", "Заявка отклонена")


@router.callback_query(F.data.startswith("lead:new:"))
@admin_only
async def cb_new(call: CallbackQuery):
    await _set_status(call, "new", "Вернули в новые")
