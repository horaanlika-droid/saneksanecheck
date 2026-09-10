"""Разделы работ (категории верхнего уровня)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, safe_edit
from app.bot.states import CatAdd, CatEdit

router = Router()


async def show_list(message: Message) -> None:
    cats = await db.list_categories()
    text = "🗂 <b>Разделы работ</b>\n\nРаздел — это верхняя категория (например: Editorial, Fine Art, Wedding). Внутри разделов живут фотосеты."
    await safe_edit(message, text, kb.categories_list(cats))


@router.callback_query(F.data == "cat")
@admin_only
async def cb_list(call: CallbackQuery):
    await call.answer()
    await show_list(call.message)  # type: ignore


async def show_card(message: Message, cat_id: int) -> None:
    cat = await db.get_category(cat_id)
    if not cat:
        await safe_edit(message, "Раздел не найден.", kb.categories_list(await db.list_categories()))
        return
    albums = await db.list_albums(cat_id)
    text = (
        f"📁 <b>{cat['title']}</b>\n"
        f"<i>{cat['subtitle'] or 'без подзаголовка'}</i>\n\n"
        f"Фотосетов: {len(albums)}"
    )
    await safe_edit(message, text, kb.category_card(cat_id))


@router.callback_query(F.data.startswith("cat:view:"))
@admin_only
async def cb_view(call: CallbackQuery):
    await call.answer()
    await show_card(call.message, int(call.data.split(":")[2]))  # type: ignore


@router.callback_query(F.data == "cat:add")
@admin_only
async def cb_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(CatAdd.title)
    await call.answer()
    await safe_edit(call.message, "➕ <b>Новый раздел</b>\n\nПришлите название:", kb.cancel_kb())  # type: ignore


@router.message(CatAdd.title, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(CatAdd.subtitle)
    await message.answer("Пришлите подзаголовок (или пропустите):", reply_markup=kb.skip_kb())


@router.message(CatAdd.subtitle, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_subtitle(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title", "")
    subtitle = "" if (message.text or "").strip() == "-" else (message.text or "").strip()
    cat_id = await db.add_category(title, subtitle)
    await state.clear()
    await message.answer(f"✅ Раздел «{title}» создан.")
    await show_card(message, cat_id)


@router.callback_query(F.data == "add:skip", CatAdd.subtitle)
@admin_only
async def cb_add_skip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    title = data.get("title", "")
    cat_id = await db.add_category(title, "")
    await state.clear()
    await call.answer("Создано")
    await show_card(call.message, cat_id)  # type: ignore


@router.callback_query(F.data.startswith("cat:ren:"))
@admin_only
async def cb_rename(call: CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split(":")[2])  # type: ignore
    await state.set_state(CatEdit.value)
    await state.update_data(id=cat_id, field="title")
    await call.answer()
    await safe_edit(call.message, "✏️ Пришлите новое <b>название</b> раздела:", kb.cancel_kb())  # type: ignore


@router.callback_query(F.data.startswith("cat:sub:"))
@admin_only
async def cb_subtitle(call: CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split(":")[2])  # type: ignore
    await state.set_state(CatEdit.value)
    await state.update_data(id=cat_id, field="subtitle")
    await call.answer()
    await safe_edit(call.message, "📝 Пришлите новый <b>подзаголовок</b> раздела:", kb.cancel_kb())  # type: ignore


@router.message(CatEdit.value, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    cat = await db.get_category(data["id"])
    if not cat:
        await state.clear()
        return
    value = (message.text or "").strip()
    if data.get("field") == "title":
        await db.update_category(data["id"], value, cat["subtitle"])
    else:
        await db.update_category(data["id"], cat["title"], value)
    await state.clear()
    await message.answer("✅ Сохранено.")
    await show_card(message, data["id"])


@router.callback_query(F.data.startswith("cat:up:"))
@admin_only
async def cb_up(call: CallbackQuery):
    await db.move_category(int(call.data.split(":")[2]), "up")  # type: ignore
    await call.answer("Перемещено")
    await show_list(call.message)  # type: ignore


@router.callback_query(F.data.startswith("cat:dn:"))
@admin_only
async def cb_dn(call: CallbackQuery):
    await db.move_category(int(call.data.split(":")[2]), "down")  # type: ignore
    await call.answer("Перемещено")
    await show_list(call.message)  # type: ignore


@router.callback_query(F.data.startswith("cat:del:"))
@admin_only
async def cb_del(call: CallbackQuery):
    cat_id = int(call.data.split(":")[2])  # type: ignore
    await call.answer()
    await safe_edit(
        call.message,  # type: ignore
        "🗑 Удалить раздел? (возможно только если в нём нет фотосетов)",
        kb.confirm_kb(f"cat:delok:{cat_id}", f"cat:view:{cat_id}"),
    )


@router.callback_query(F.data.startswith("cat:delok:"))
@admin_only
async def cb_delok(call: CallbackQuery):
    cat_id = int(call.data.split(":")[2])  # type: ignore
    ok = await db.delete_category(cat_id)
    await call.answer("Удалено" if ok else "В разделе есть фотосеты — сначала удалите или перенесите их", show_alert=not ok)
    await show_list(call.message)  # type: ignore
