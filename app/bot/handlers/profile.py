"""Профиль: имя, о себе, контакты, соцсети, настройки приложения."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, safe_edit, short
from app.bot.states import ProfileEdit, Upload

router = Router()


@router.callback_query(F.data == "pf")
@admin_only
async def cb_profile(call: CallbackQuery):
    await call.answer()
    settings = await db.all_settings()
    text = (
        "👤 <b>Профиль и контакты</b>\n\n"
        f"✨ {settings.get('brand_name', '—')}\n"
        f"💫 {short(settings.get('tagline', ''), 60)}\n"
        f"📞 {settings.get('phone', '—')} · 📍 {short(settings.get('city', ''), 40)}\n\n"
        "Нажмите на поле, чтобы изменить:"
    )
    await safe_edit(call.message, text, kb.profile_menu(settings))  # type: ignore


@router.callback_query(F.data.startswith("pf:set:"))
@admin_only
async def cb_profile_set(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":", 2)[2]  # type: ignore
    label = kb.PROFILE_LABELS.get(key, key)
    hint = next((h for k, _, h in kb.PROFILE_FIELDS if k == key), "")
    current = await db.get_setting(key, "")
    await state.set_state(ProfileEdit.value)
    await state.update_data(key=key)
    await call.answer()
    text = f"{label}\n\n<i>{hint}</i>\n\nТекущее значение:\n<code>{current or '—'}</code>\n\nПришлите новое значение:"
    await safe_edit(call.message, text, kb.cancel_kb())  # type: ignore


@router.message(ProfileEdit.value, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_profile_value(message: Message, state: FSMContext):
    data = await state.get_data()
    key = data.get("key", "")
    value = (message.text or "").strip()
    await db.set_setting(key, value)
    # если поменяли адрес приложения — сразу перепушиваем кнопку меню
    if key == "webapp_url" and value and message.bot:
        try:
            from app.bot.bot import push_bot_settings
            await push_bot_settings(message.bot)
        except Exception:
            pass
    await state.clear()
    label = kb.PROFILE_LABELS.get(key, key)
    await message.answer(f"✅ {label} обновлено.")
    settings = await db.all_settings()
    await message.answer("👤 <b>Профиль и контакты</b>\n\nНажмите на поле, чтобы изменить:", reply_markup=kb.profile_menu(settings))


@router.callback_query(F.data == "pf:avatar")
@admin_only
async def cb_avatar(call: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.waiting)
    await state.update_data(target="avatar", id=0, count=0, pending=[])
    await call.answer()
    await call.message.answer("🖼 Пришлите фото для <b>аватарки</b>:", reply_markup=kb.done_reply_kb())  # type: ignore


@router.callback_query(F.data == "pf:hero")
@admin_only
async def cb_hero(call: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.waiting)
    await state.update_data(target="hero", id=0, count=0, pending=[])
    await call.answer()
    await call.message.answer("🌄 Пришлите фото для <b>главного экрана</b>:", reply_markup=kb.done_reply_kb())  # type: ignore


@router.callback_query(F.data == "pf:toggle:booking")
@admin_only
async def cb_toggle_booking(call: CallbackQuery):
    current = await db.get_setting("booking_enabled", "1")
    await db.set_setting("booking_enabled", "0" if current == "1" else "1")
    await call.answer("Готово")
    settings = await db.all_settings()
    on = settings.get("booking_enabled") == "1"
    text = f"👤 <b>Профиль и контакты</b>\n\nФорма записи: {'🟢 включена' if on else '🔴 выключена'}\n\nНажмите на поле, чтобы изменить:"
    await safe_edit(call.message, text, kb.profile_menu(settings))  # type: ignore
