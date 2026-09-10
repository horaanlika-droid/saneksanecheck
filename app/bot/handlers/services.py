"""Услуги: названия, описания, цены, обложки и прикреплённые фото."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, delete_upload_files, safe_edit, short
from app.bot.states import SvcAdd, SvcEdit, Upload

router = Router()


async def show_list(message: Message) -> None:
    services = await db.list_services()
    await safe_edit(message, "💼 <b>Услуги</b>\n\n🟢 — показывается на сайте, 🔴 — скрыта.", kb.services_list(services))


@router.callback_query(F.data == "svc")
@admin_only
async def cb_list(call: CallbackQuery):
    await call.answer()
    await show_list(call.message)  # type: ignore


async def show_card(message: Message, service_id: int) -> None:
    svc = await db.get_service(service_id)
    if not svc:
        await show_list(message)
        return
    photos = await db.list_photos(service_id=service_id)
    dot = "🟢" if svc["is_active"] else "🔴"
    text = (
        f"{dot} <b>{svc['title']}</b>\n"
        f"💰 {svc['price'] or '—'}"
        + (f" ({svc['price_note']})" if svc["price_note"] else "")
        + (f"\n⏱ {svc['duration']}" if svc["duration"] else "")
        + f"\n\n{svc['description'] or '<i>без описания</i>'}"
        f"\n\n🖼 Обложка: {'есть' if svc['cover_path'] else 'нет'} · 📷 Фото: {len(photos)}"
    )
    await safe_edit(message, text, kb.service_card(svc, len(photos)))


@router.callback_query(F.data.startswith("svc:view:"))
@admin_only
async def cb_view(call: CallbackQuery):
    await call.answer()
    await show_card(call.message, int(call.data.split(":")[2]))  # type: ignore


# ------------------------------------------------------------ создание
@router.callback_query(F.data == "svc:add")
@admin_only
async def cb_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(SvcAdd.title)
    await call.answer()
    await safe_edit(call.message, "➕ <b>Новая услуга</b>\n\nПришлите название:", kb.cancel_kb())  # type: ignore


@router.message(SvcAdd.title, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(SvcAdd.description)
    await message.answer("Пришлите описание услуги (что входит, каждый пункт с новой строки):", reply_markup=kb.skip_kb())


@router.message(SvcAdd.description, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_description(message: Message, state: FSMContext):
    await state.update_data(description="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    await state.set_state(SvcAdd.price)
    await message.answer("Пришлите цену (например: от 45 000 ₽):", reply_markup=kb.skip_kb())


@router.message(SvcAdd.price, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_price(message: Message, state: FSMContext):
    await state.update_data(price="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    await state.set_state(SvcAdd.price_note)
    await message.answer("Уточнение к цене (например: финальная цена — после брифа):", reply_markup=kb.skip_kb())


@router.message(SvcAdd.price_note, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_price_note(message: Message, state: FSMContext):
    await state.update_data(price_note="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    await state.set_state(SvcAdd.duration)
    await message.answer("Длительность (например: 2–3 часа):", reply_markup=kb.skip_kb())


@router.message(SvcAdd.duration, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_duration(message: Message, state: FSMContext):
    await state.update_data(duration="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    data = await state.get_data()
    sid = await db.add_service(data.get("title", ""), data.get("description", ""), data.get("price", ""), data.get("price_note", ""), data.get("duration", ""))
    await state.clear()
    await message.answer("✅ Услуга создана.")
    await show_card(message, sid)


@router.callback_query(F.data == "add:skip", StateFilter(SvcAdd.description, SvcAdd.price, SvcAdd.price_note, SvcAdd.duration))
@admin_only
async def cb_add_skip(call: CallbackQuery, state: FSMContext):
    cur = await state.get_state()
    await call.answer()
    if cur == SvcAdd.description:
        await state.update_data(description="")
        await state.set_state(SvcAdd.price)
        await safe_edit(call.message, "Пришлите цену (например: от 45 000 ₽):", kb.skip_kb())  # type: ignore
    elif cur == SvcAdd.price:
        await state.update_data(price="")
        await state.set_state(SvcAdd.price_note)
        await safe_edit(call.message, "Уточнение к цене:", kb.skip_kb())  # type: ignore
    elif cur == SvcAdd.price_note:
        await state.update_data(price_note="")
        await state.set_state(SvcAdd.duration)
        await safe_edit(call.message, "Длительность (например: 2–3 часа):", kb.skip_kb())  # type: ignore
    else:
        await state.update_data(duration="")
        data = await state.get_data()
        sid = await db.add_service(data.get("title", ""), data.get("description", ""), data.get("price", ""), data.get("price_note", ""), data.get("duration", ""))
        await state.clear()
        await show_card(call.message, sid)  # type: ignore


# ------------------------------------------------------------ редактирование
@router.callback_query(F.data.startswith("svc:edit:"))
@admin_only
async def cb_edit(call: CallbackQuery, state: FSMContext):
    _, _, sid, field = call.data.split(":")  # type: ignore
    svc = await db.get_service(int(sid))
    if not svc:
        await call.answer("Не найдено", show_alert=True)
        return
    await state.set_state(SvcEdit.value)
    await state.update_data(id=int(sid), field=field)
    await call.answer()
    label = kb.SVC_FIELD_LABELS.get(field, field)
    await safe_edit(call.message, f"✏️ Пришлите {label}:\n\nТекущее: <code>{short(svc.get(field, ''), 200) or '—'}</code>", kb.cancel_kb())  # type: ignore


@router.message(SvcEdit.value, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_service(data["id"], **{data["field"]: (message.text or "").strip()})
    await state.clear()
    await message.answer("✅ Сохранено.")
    await show_card(message, data["id"])


@router.callback_query(F.data.startswith("svc:toggle:"))
@admin_only
async def cb_toggle(call: CallbackQuery):
    sid = int(call.data.split(":")[2])  # type: ignore
    svc = await db.get_service(sid)
    if svc:
        await db.update_service(sid, is_active=0 if svc["is_active"] else 1)
    await call.answer("Готово")
    await show_card(call.message, sid)  # type: ignore


@router.callback_query(F.data.startswith("svc:uppos:"))
@admin_only
async def cb_uppos(call: CallbackQuery):
    await db.move_service(int(call.data.split(":")[2]), "up")  # type: ignore
    await call.answer("Перемещено")
    await show_list(call.message)  # type: ignore


@router.callback_query(F.data.startswith("svc:dnpos:"))
@admin_only
async def cb_dn(call: CallbackQuery):
    await db.move_service(int(call.data.split(":")[2]), "down")  # type: ignore
    await call.answer("Перемещено")
    await show_list(call.message)  # type: ignore


@router.callback_query(F.data.startswith("svc:del:"))
@admin_only
async def cb_del(call: CallbackQuery):
    sid = int(call.data.split(":")[2])  # type: ignore
    await call.answer()
    await safe_edit(call.message, "🗑 Удалить услугу вместе с прикреплёнными фото? Она пропадёт с сайта.", kb.confirm_kb(f"svc:delok:{sid}", f"svc:view:{sid}"))  # type: ignore


@router.callback_query(F.data.startswith("svc:delok:"))
@admin_only
async def cb_delok(call: CallbackQuery):
    sid = int(call.data.split(":")[2])  # type: ignore
    paths = await db.delete_service(sid)
    await delete_upload_files(paths)
    await call.answer("Удалено")
    await show_list(call.message)  # type: ignore


# ------------------------------------------------------------ фото услуги
@router.callback_query(F.data.startswith("svc:cover:"))
@admin_only
async def cb_cover(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[2])  # type: ignore
    await state.set_state(Upload.waiting)
    await state.update_data(target="service_cover", id=sid, count=0, pending=[])
    await call.answer()
    await call.message.answer("🖼 Пришлите фото для <b>обложки услуги</b>:", reply_markup=kb.done_reply_kb())  # type: ignore


@router.callback_query(F.data.startswith("svc:up:"))
@admin_only
async def cb_upload(call: CallbackQuery, state: FSMContext):
    sid = int(call.data.split(":")[2])  # type: ignore
    await state.set_state(Upload.waiting)
    await state.update_data(target="service", id=sid, count=0)
    await call.answer()
    await call.message.answer("📥 Присылайте фото для услуги. Когда закончите — «✅ Готово».", reply_markup=kb.done_reply_kb())  # type: ignore


@router.callback_query(F.data.startswith("svc:ph:"))
@admin_only
async def cb_photos(call: CallbackQuery):
    sid = int(call.data.split(":")[2])  # type: ignore
    svc = await db.get_service(sid)
    photos = await db.list_photos(service_id=sid)
    await call.answer()
    title = svc["title"] if svc else "?"
    await safe_edit(call.message, f"📷 Фото услуги — «{title}» ({len(photos)}):\n\nНажмите на фото, чтобы подписать, переместить или удалить.", kb.photos_list(photos, f"s{sid}", f"svc:view:{sid}"))  # type: ignore
