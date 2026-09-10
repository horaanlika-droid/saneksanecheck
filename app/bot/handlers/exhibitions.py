"""Выставки и награды."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, safe_edit, short
from app.bot.states import ExAdd, ExEdit

router = Router()


async def show_list(message: Message) -> None:
    items = await db.list_exhibitions()
    await safe_edit(message, "🏆 <b>Выставки и награды</b>\n\nМеждународные выставки, фестивали, премии.", kb.exhibitions_list(items))


@router.callback_query(F.data == "ex")
@admin_only
async def cb_list(call: CallbackQuery):
    await call.answer()
    await show_list(call.message)  # type: ignore


async def show_card(message: Message, ex_id: int) -> None:
    ex = await db.get_exhibition(ex_id)
    if not ex:
        await show_list(message)
        return
    meta = " · ".join(x for x in (ex["place"], ex["year"]) if x)
    text = f"🏆 <b>{ex['title']}</b>" + (f"\n{meta}" if meta else "") + f"\n\n{ex['description'] or '<i>без описания</i>'}"
    await safe_edit(message, text, kb.exhibition_card(ex_id))


@router.callback_query(F.data.startswith("ex:view:"))
@admin_only
async def cb_view(call: CallbackQuery):
    await call.answer()
    await show_card(call.message, int(call.data.split(":")[2]))  # type: ignore


@router.callback_query(F.data == "ex:add")
@admin_only
async def cb_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(ExAdd.title)
    await call.answer()
    await safe_edit(call.message, "➕ Пришлите название выставки / награды:", kb.cancel_kb())  # type: ignore


@router.message(ExAdd.title, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(ExAdd.place)
    await message.answer("Место (например: Венеция, Италия):", reply_markup=kb.skip_kb())


@router.message(ExAdd.place, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_place(message: Message, state: FSMContext):
    await state.update_data(place="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    await state.set_state(ExAdd.year)
    await message.answer("Год:", reply_markup=kb.skip_kb())


@router.message(ExAdd.year, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_year(message: Message, state: FSMContext):
    await state.update_data(year="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    await state.set_state(ExAdd.description)
    await message.answer("Описание (или пропустите):", reply_markup=kb.skip_kb())


@router.message(ExAdd.description, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_description(message: Message, state: FSMContext):
    await state.update_data(description="" if (message.text or "").strip() == "-" else (message.text or "").strip())
    data = await state.get_data()
    ex_id = await db.add_exhibition(data.get("title", ""), data.get("place", ""), data.get("year", ""), data.get("description", ""))
    await state.clear()
    await message.answer("✅ Добавлено.")
    await show_card(message, ex_id)


@router.callback_query(F.data == "add:skip", StateFilter(ExAdd.place, ExAdd.year, ExAdd.description))
@admin_only
async def cb_add_skip(call: CallbackQuery, state: FSMContext):
    cur = await state.get_state()
    await call.answer()
    if cur == ExAdd.place:
        await state.update_data(place="")
        await state.set_state(ExAdd.year)
        await safe_edit(call.message, "Год:", kb.skip_kb())  # type: ignore
    elif cur == ExAdd.year:
        await state.update_data(year="")
        await state.set_state(ExAdd.description)
        await safe_edit(call.message, "Описание (или пропустите):", kb.skip_kb())  # type: ignore
    else:
        await state.update_data(description="")
        data = await state.get_data()
        ex_id = await db.add_exhibition(data.get("title", ""), data.get("place", ""), data.get("year", ""), data.get("description", ""))
        await state.clear()
        await show_card(call.message, ex_id)  # type: ignore


@router.callback_query(F.data.startswith("ex:edit:"))
@admin_only
async def cb_edit(call: CallbackQuery, state: FSMContext):
    _, _, eid, field = call.data.split(":")  # type: ignore
    ex = await db.get_exhibition(int(eid))
    if not ex:
        await call.answer("Не найдено", show_alert=True)
        return
    await state.set_state(ExEdit.value)
    await state.update_data(id=int(eid), field=field)
    await call.answer()
    await safe_edit(call.message, f"✏️ Пришлите {kb.EX_FIELD_LABELS.get(field, field)}:\n\nТекущее: <code>{short(ex.get(field, ''), 200) or '—'}</code>", kb.cancel_kb())  # type: ignore


@router.message(ExEdit.value, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_exhibition(data["id"], **{data["field"]: (message.text or "").strip()})
    await state.clear()
    await message.answer("✅ Сохранено.")
    await show_card(message, data["id"])


@router.callback_query(F.data.startswith("ex:up:"))
@admin_only
async def cb_up(call: CallbackQuery):
    await db.move_exhibition(int(call.data.split(":")[2]), "up")  # type: ignore
    await call.answer("Перемещено")
    await show_list(call.message)  # type: ignore


@router.callback_query(F.data.startswith("ex:dn:"))
@admin_only
async def cb_dn(call: CallbackQuery):
    await db.move_exhibition(int(call.data.split(":")[2]), "down")  # type: ignore
    await call.answer("Перемещено")
    await show_list(call.message)  # type: ignore


@router.callback_query(F.data.startswith("ex:del:"))
@admin_only
async def cb_del(call: CallbackQuery):
    eid = int(call.data.split(":")[2])  # type: ignore
    await call.answer()
    await safe_edit(call.message, "🗑 Удалить запись?", kb.confirm_kb(f"ex:delok:{eid}", f"ex:view:{eid}"))  # type: ignore


@router.callback_query(F.data.startswith("ex:delok:"))
@admin_only
async def cb_delok(call: CallbackQuery):
    await db.delete_exhibition(int(call.data.split(":")[2]))  # type: ignore
    await call.answer("Удалено")
    await show_list(call.message)  # type: ignore
