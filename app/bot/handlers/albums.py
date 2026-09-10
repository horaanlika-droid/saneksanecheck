"""Фотосеты (альбомы) — подкатегории внутри разделов."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, delete_upload_files, safe_edit, short
from app.bot.states import AlbAdd, AlbEdit, Upload

router = Router()


async def show_roots(message: Message) -> None:
    cats = await db.list_categories()
    if not cats:
        await safe_edit(message, "📸 <b>Фотосеты</b>\n\nСначала создайте раздел в «🗂 Разделы работ».", kb.back_to().as_markup())
        return
    await safe_edit(
        message,
        "📸 <b>Фотосеты</b>\n\nФотосет — это серия работ внутри раздела (например: выставка, съёмка, проект). Выберите раздел:",
        kb.album_categories(cats),
    )


@router.callback_query(F.data == "alb")
@admin_only
async def cb_root(call: CallbackQuery):
    await call.answer()
    await show_roots(call.message)  # type: ignore


async def show_album_list(message: Message, cat_id: int) -> None:
    cat = await db.get_category(cat_id)
    if not cat:
        await show_roots(message)
        return
    albums = await db.list_albums(cat_id)
    counts: dict[int, int] = {}
    for a in albums:
        counts[a["id"]] = len(await db.list_photos(album_id=a["id"]))
    text = f"📁 <b>{cat['title']}</b>\n\nФотосетов: {len(albums)}"
    await safe_edit(message, text, kb.albums_list(albums, cat_id, counts))


@router.callback_query(F.data.startswith("alb:cat:"))
@admin_only
async def cb_cat_albums(call: CallbackQuery):
    await call.answer()
    await show_album_list(call.message, int(call.data.split(":")[2]))  # type: ignore


async def show_album_card(message: Message, album_id: int) -> None:
    alb = await db.get_album(album_id)
    if not alb:
        await safe_edit(message, "Фотосет не найден.", kb.back_to("alb").as_markup())
        return
    photos = await db.list_photos(album_id=album_id)
    cat = await db.get_category(alb["category_id"])
    vis = "👁 виден" if alb["is_visible"] else "🙈 скрыт"
    cover = next((p for p in photos if p["id"] == alb["cover_photo_id"]), None)
    text = (
        f"📸 <b>{alb['title']}</b> · {vis}\n"
        f"📁 {cat['title'] if cat else '—'}"
    )
    meta = " · ".join(x for x in (alb["location"], alb["year"]) if x)
    if meta:
        text += f" · {meta}"
    text += f"\n\n{alb['description'] or '<i>без описания</i>'}\n\nФотографий: {len(photos)}"
    if cover:
        text += " · ⭐ обложка задана"
    elif photos:
        text += " · обложка: первое фото"
    await safe_edit(message, text, kb.album_card(alb, len(photos)))


@router.callback_query(F.data.startswith("alb:view:"))
@admin_only
async def cb_view(call: CallbackQuery):
    await call.answer()
    await show_album_card(call.message, int(call.data.split(":")[2]))  # type: ignore


# ------------------------------------------------------------ создание
@router.callback_query(F.data.startswith("alb:add:"))
@admin_only
async def cb_add(call: CallbackQuery, state: FSMContext):
    cat_id = int(call.data.split(":")[2])  # type: ignore
    await state.set_state(AlbAdd.title)
    await state.update_data(category_id=cat_id)
    await call.answer()
    await safe_edit(call.message, "➕ <b>Новый фотосет</b>\n\nПришлите название:", kb.cancel_kb())  # type: ignore


@router.message(AlbAdd.title, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AlbAdd.description)
    await message.answer("Пришлите описание фотосета (или пропустите):", reply_markup=kb.skip_kb())


@router.message(AlbAdd.description, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_description(message: Message, state: FSMContext):
    value = "" if (message.text or "").strip() == "-" else (message.text or "").strip()
    await state.update_data(description=value)
    await state.set_state(AlbAdd.location)
    await message.answer("Пришлите локацию (например: Венеция, Италия):", reply_markup=kb.skip_kb())


@router.message(AlbAdd.location, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_location(message: Message, state: FSMContext):
    value = "" if (message.text or "").strip() == "-" else (message.text or "").strip()
    await state.update_data(location=value)
    await state.set_state(AlbAdd.year)
    await message.answer("Пришлите год (например: 2025):", reply_markup=kb.skip_kb())


async def _finish_add(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    album_id = await db.add_album(
        data["category_id"], data.get("title", ""),
        data.get("description", ""), data.get("location", ""), data.get("year", ""),
    )
    await state.clear()
    await message.answer("✅ Фотосет создан. Теперь загрузите фотографии:")
    await state.set_state(Upload.waiting)
    await state.update_data(target="album", id=album_id, count=0)
    await message.answer(
        "📥 Присылайте фото (по одному или альбомом). Когда закончите — нажмите «✅ Готово».",
        reply_markup=kb.done_reply_kb(),
    )


@router.message(AlbAdd.year, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_add_year(message: Message, state: FSMContext):
    value = "" if (message.text or "").strip() == "-" else (message.text or "").strip()
    await state.update_data(year=value)
    await _finish_add(message, state)


@router.callback_query(F.data == "add:skip", StateFilter(AlbAdd.description, AlbAdd.location, AlbAdd.year))
@admin_only
async def cb_add_skip(call: CallbackQuery, state: FSMContext):
    cur = await state.get_state()
    await call.answer()
    if cur == AlbAdd.description:
        await state.update_data(description="")
        await state.set_state(AlbAdd.location)
        await safe_edit(call.message, "Пришлите локацию (например: Венеция, Италия):", kb.skip_kb())  # type: ignore
    elif cur == AlbAdd.location:
        await state.update_data(location="")
        await state.set_state(AlbAdd.year)
        await safe_edit(call.message, "Пришлите год (например: 2025):", kb.skip_kb())  # type: ignore
    else:
        await state.update_data(year="")
        await _finish_add(call.message, state)  # type: ignore


# ------------------------------------------------------------ редактирование
@router.callback_query(F.data.startswith("alb:edit:"))
@admin_only
async def cb_edit(call: CallbackQuery, state: FSMContext):
    _, _, aid, field = call.data.split(":")  # type: ignore
    alb = await db.get_album(int(aid))
    if not alb:
        await call.answer("Не найдено", show_alert=True)
        return
    await state.set_state(AlbEdit.value)
    await state.update_data(id=int(aid), field=field)
    await call.answer()
    label = kb.ALBUM_FIELD_LABELS.get(field, field)
    current = alb.get(field, "")
    await safe_edit(call.message, f"✏️ Пришлите {label}:\n\nТекущее: <code>{short(current, 200) or '—'}</code>", kb.cancel_kb())  # type: ignore


@router.message(AlbEdit.value, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_album(data["id"], **{data["field"]: (message.text or "").strip()})
    await state.clear()
    await message.answer("✅ Сохранено.")
    await show_album_card(message, data["id"])


@router.callback_query(F.data.startswith("alb:movecat:"))
@admin_only
async def cb_movecat(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    cats = await db.list_categories()
    b = InlineKeyboardBuilder()
    for c in cats:
        b.button(text=f"📁 {c['title']}", callback_data=f"alb:setcat:{aid}:{c['id']}")
    b.button(text="⬅️ Назад", callback_data=f"alb:view:{aid}")
    b.adjust(1)
    await call.answer()
    await safe_edit(call.message, "📁 Выберите новый раздел:", b.as_markup())  # type: ignore


@router.callback_query(F.data.startswith("alb:setcat:"))
@admin_only
async def cb_setcat(call: CallbackQuery):
    _, _, aid, cid = call.data.split(":")  # type: ignore
    await db.update_album(int(aid), category_id=int(cid))
    await call.answer("Раздел изменён")
    await show_album_card(call.message, int(aid))  # type: ignore


@router.callback_query(F.data.startswith("alb:vis:"))
@admin_only
async def cb_vis(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    alb = await db.get_album(aid)
    if alb:
        await db.update_album(aid, is_visible=0 if alb["is_visible"] else 1)
    await call.answer("Готово")
    await show_album_card(call.message, aid)  # type: ignore


@router.callback_query(F.data.startswith("alb:uppos:"))
@admin_only
async def cb_uppos(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    await db.move_album(aid, "up")
    await call.answer("Перемещено")
    alb = await db.get_album(aid)
    if alb:
        await show_album_list(call.message, alb["category_id"])  # type: ignore


@router.callback_query(F.data.startswith("alb:dnpos:"))
@admin_only
async def cb_dn(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    await db.move_album(aid, "down")
    await call.answer("Перемещено")
    alb = await db.get_album(aid)
    if alb:
        await show_album_list(call.message, alb["category_id"])  # type: ignore


@router.callback_query(F.data.startswith("alb:del:"))
@admin_only
async def cb_del(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    n = len(await db.list_photos(album_id=aid))
    await call.answer()
    await safe_edit(
        call.message,  # type: ignore
        f"🗑 Удалить фотосет и все его фотографии ({n} шт.)? Они пропадут с сайта.",
        kb.confirm_kb(f"alb:delok:{aid}", f"alb:view:{aid}"),
    )


@router.callback_query(F.data.startswith("alb:delok:"))
@admin_only
async def cb_delok(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    alb = await db.get_album(aid)
    paths = await db.delete_album(aid)
    await delete_upload_files(paths)
    await call.answer("Удалено")
    if alb:
        await show_album_list(call.message, alb["category_id"])  # type: ignore
    else:
        await show_roots(call.message)  # type: ignore


# ------------------------------------------------------------ фото
@router.callback_query(F.data.startswith("alb:up:"))
@admin_only
async def cb_upload(call: CallbackQuery, state: FSMContext):
    aid = int(call.data.split(":")[2])  # type: ignore
    await state.set_state(Upload.waiting)
    await state.update_data(target="album", id=aid, count=0)
    await call.answer()
    await call.message.answer(  # type: ignore
        "📥 Присылайте фото (по одному или альбомом). Когда закончите — нажмите «✅ Готово».",
        reply_markup=kb.done_reply_kb(),
    )


@router.callback_query(F.data.startswith("alb:ph:"))
@admin_only
async def cb_photos(call: CallbackQuery):
    aid = int(call.data.split(":")[2])  # type: ignore
    alb = await db.get_album(aid)
    photos = await db.list_photos(album_id=aid)
    await call.answer()
    text = f"🖼 Фотографии — «{alb['title']}» ({len(photos)}):\n\nНажмите на фото, чтобы подписать, переместить или удалить." if alb else "Фотосет не найден"
    await safe_edit(call.message, text, kb.photos_list(photos, f"a{aid}", f"alb:view:{aid}"))  # type: ignore
