"""Статистика, бэкап, администраторы, отмена."""

from __future__ import annotations

import time
import zipfile

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, safe_edit
from app.bot.handlers.start import get_counts, show_panel
from app.bot.states import AdminAdd
from app.config import get_settings

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data == "add:cancel")
async def cb_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer("Отменено")
    if call.from_user and await db.is_admin(call.from_user.id):
        await show_panel(call.message)  # type: ignore
    else:
        try:
            await call.message.delete()  # type: ignore
        except Exception:
            pass


@router.callback_query(F.data == "stats")
@admin_only
async def cb_stats(call: CallbackQuery):
    await call.answer()
    counts = await get_counts()
    settings = get_settings()
    db_size = settings.db_path.stat().st_size if settings.db_path.exists() else 0
    uploads = list(settings.upload_dir.glob("*")) if settings.upload_dir.exists() else []
    up_size = sum(f.stat().st_size for f in uploads if f.is_file())
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"🗂 Разделов: {counts['categories']}\n"
        f"📸 Фотосетов: {counts['albums']}\n"
        f"🖼 Всего фото: {counts['photos']} (файлов: {len(uploads)})\n"
        f"💼 Услуг: {counts['services']}\n"
        f"🏆 Выставок: {counts['exhibitions']}\n"
        f"💬 Новых заявок: {counts['new_leads']}\n\n"
        f"💾 База: {db_size / 1024:.0f} KB · Фото: {up_size / 1024 / 1024:.1f} MB"
    )
    await safe_edit(call.message, text, kb.back_to().as_markup())  # type: ignore


def _make_backup() -> str | None:
    settings = get_settings()
    if not settings.db_path.exists():
        return None
    name = f"backup_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    out = settings.data_dir / name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(settings.db_path, "app.db")
        if settings.upload_dir.exists():
            for f in settings.upload_dir.iterdir():
                if f.is_file():
                    z.write(f, f"uploads/{f.name}")
    return str(out)


async def _send_backup(message: Message) -> None:
    path = _make_backup()
    if not path:
        await message.answer("⚠️ База данных ещё не создана.")
        return
    try:
        await message.answer_document(FSInputFile(path), caption="💾 Бэкап: база + все фотографии")
    finally:
        try:
            import os
            os.unlink(path)
        except OSError:
            pass


@router.message(Command("backup"))
@admin_only
async def cmd_backup(message: Message):
    await message.answer("💾 Собираю бэкап...")
    await _send_backup(message)


@router.callback_query(F.data == "backup")
@admin_only
async def cb_backup(call: CallbackQuery):
    await call.answer()
    await call.message.answer("💾 Собираю бэкап...")  # type: ignore
    await _send_backup(call.message)  # type: ignore


# ------------------------------------------------------------ администраторы
@router.callback_query(F.data == "admins")
@admin_only
async def cb_admins(call: CallbackQuery):
    await call.answer()
    await safe_edit(
        call.message,  # type: ignore
        "👥 <b>Администраторы</b>\n\n🔒 — задан через ADMIN_IDS на хостинге (убрать можно только там).",
        kb.admins_list(await db.list_admin_ids(), get_settings().admin_ids),
    )


@router.callback_query(F.data == "adm:add")
@admin_only
async def cb_admin_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(AdminAdd.waiting)
    await call.answer()
    await safe_edit(call.message, "➕ Пришлите <b>telegram user id</b> нового админа (цифры):", kb.cancel_kb())  # type: ignore


@router.message(AdminAdd.waiting, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_admin_add(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("⚠️ Нужен числовой id. Узнать его можно через @userinfobot — попросите человека написать туда.")
        return
    await db.add_admin(int(text))
    await state.clear()
    await message.answer(f"✅ {text} теперь администратор.")
    await message.answer(
        "👥 <b>Администраторы</b>",
        reply_markup=kb.admins_list(await db.list_admin_ids(), get_settings().admin_ids),
    )


@router.callback_query(F.data.startswith("adm:del:"))
@admin_only
async def cb_admin_del(call: CallbackQuery):
    uid = int(call.data.split(":")[2])  # type: ignore
    if uid in get_settings().admin_ids:
        await call.answer("Этого админа можно убрать только через ADMIN_IDS на хостинге", show_alert=True)
        return
    await db.remove_admin(uid)
    await call.answer("Убран")
    await safe_edit(call.message, "👥 <b>Администраторы</b>", kb.admins_list(await db.list_admin_ids(), get_settings().admin_ids))  # type: ignore


@router.callback_query(F.data.startswith("adm:noop:"))
@admin_only
async def cb_admin_noop(call: CallbackQuery):
    await call.answer()


@router.callback_query(F.data == "adm:help")
@admin_only
async def cb_admin_help(call: CallbackQuery):
    await call.answer(
        "Попросите человека написать боту @userinfobot — он покажет числовой id. Затем добавьте его здесь.",
        show_alert=True,
    )
