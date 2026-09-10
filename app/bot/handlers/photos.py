"""Избранные фото (standalone), просмотр/действия с фото и движок загрузки."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, delete_upload_files, safe_edit, short
from app.bot.media import copy_upload, save_tg_photo
from app.bot.states import PhotoCaption, Upload
from app.config import get_settings

router = Router()


def _back_for_ctx(ctx: str) -> str:
    return f"ph:back:{ctx}"


async def _list_text_and_kb(ctx: str):
    """Текст и клавиатура списка фотографий для контекста."""
    if ctx == "sel":
        photos = await db.list_photos(standalone=True)
        text = (
            f"🖼 <b>Избранное</b> ({len(photos)})\n\n"
            "Отдельные фотографии вне фотосетов — они показываются на сайте лентой «Selected». "
            "Нажмите на фото, чтобы подписать, переместить или удалить."
        )
        markup = kb.photos_list(photos, "sel", "menu")
        markup.inline_keyboard.insert(-1, [InlineKeyboardButton(text="📥 Загрузить фото", callback_data="sel:add")])
        return text, markup
    if ctx.startswith("a"):
        aid = int(ctx[1:])
        alb = await db.get_album(aid)
        photos = await db.list_photos(album_id=aid)
        title = alb["title"] if alb else "?"
        text = f"🖼 Фотографии — «{title}» ({len(photos)}):\n\nНажмите на фото, чтобы подписать, переместить или удалить."
        return text, kb.photos_list(photos, ctx, f"alb:view:{aid}")
    if ctx.startswith("s"):
        sid = int(ctx[1:])
        svc = await db.get_service(sid)
        photos = await db.list_photos(service_id=sid)
        title = svc["title"] if svc else "?"
        text = f"📷 Фото услуги — «{title}» ({len(photos)}):\n\nНажмите на фото, чтобы подписать, переместить или удалить."
        return text, kb.photos_list(photos, ctx, f"svc:view:{sid}")
    return "?", kb.back_to().as_markup()


async def _is_cover(photo: dict, ctx: str) -> bool:
    if ctx.startswith("a"):
        alb = await db.get_album(int(ctx[1:]))
        return bool(alb) and alb["cover_photo_id"] == photo["id"]
    return False


async def _photo_caption(photo: dict, ctx: str) -> str:
    star = " ⭐ <i>обложка</i>" if await _is_cover(photo, ctx) else ""
    size = f"{photo['width']}×{photo['height']}" if photo["width"] else ""
    cap = photo["caption"] or "—"
    return f"🖼 <b>Фото #{photo['id']}</b>{star}\n{size}\n\nПодпись: {cap}"


@router.callback_query(F.data == "sel")
@admin_only
async def cb_standalone(call: CallbackQuery):
    await call.answer()
    text, markup = await _list_text_and_kb("sel")
    await safe_edit(call.message, text, markup)  # type: ignore


@router.callback_query(F.data == "sel:add")
@admin_only
async def cb_standalone_add(call: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.waiting)
    await state.update_data(target="standalone", id=0, count=0)
    await call.answer()
    await call.message.answer(  # type: ignore
        "📥 Присылайте отдельные фото для ленты «Избранное». Когда закончите — «✅ Готово».",
        reply_markup=kb.done_reply_kb(),
    )


# ------------------------------------------------------------ просмотр фото
@router.callback_query(F.data.startswith("ph:view:"))
@admin_only
async def cb_photo_view(call: CallbackQuery):
    _, _, pid, ctx = call.data.split(":")  # type: ignore
    photo = await db.get_photo(int(pid))
    if not photo:
        await call.answer("Фото не найдено", show_alert=True)
        return
    await call.answer()
    fpath = get_settings().upload_dir / photo["path"]
    markup = kb.photo_card(photo["id"], ctx, _back_for_ctx(ctx), await _is_cover(photo, ctx))
    caption = await _photo_caption(photo, ctx)
    if fpath.exists():
        await call.message.answer_photo(FSInputFile(fpath), caption=caption, reply_markup=markup)  # type: ignore
    elif photo["file_id"]:
        await call.message.answer_photo(photo["file_id"], caption=caption, reply_markup=markup)  # type: ignore
    else:
        await call.message.answer(caption + "\n\n<i>⚠️ файл отсутствует на диске</i>", reply_markup=markup)  # type: ignore


@router.callback_query(F.data.startswith("ph:back:"))
@admin_only
async def cb_photo_back(call: CallbackQuery):
    ctx = call.data.split(":", 2)[2]  # type: ignore
    await call.answer()
    try:
        await call.message.delete()  # type: ignore
    except Exception:
        pass
    text, markup = await _list_text_and_kb(ctx)
    await call.message.answer(text, reply_markup=markup)  # type: ignore


@router.callback_query(F.data.startswith("ph:cap:"))
@admin_only
async def cb_photo_cap(call: CallbackQuery, state: FSMContext):
    _, _, pid, ctx = call.data.split(":")  # type: ignore
    await state.set_state(PhotoCaption.value)
    await state.update_data(photo_id=int(pid), ctx=ctx,
                            chat_id=call.message.chat.id, msg_id=call.message.message_id)  # type: ignore
    await call.answer()
    await call.message.answer("✏️ Пришлите подпись для фото (или «-», чтобы убрать):")  # type: ignore


@router.message(PhotoCaption.value, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_photo_cap(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    caption = "" if (message.text or "").strip() == "-" else (message.text or "").strip()
    await db.update_photo_caption(data["photo_id"], caption)
    await state.clear()
    photo = await db.get_photo(data["photo_id"])
    if photo:
        try:
            await bot.edit_message_caption(
                chat_id=data["chat_id"], message_id=data["msg_id"],
                caption=await _photo_caption(photo, data["ctx"]),
                reply_markup=kb.photo_card(photo["id"], data["ctx"], _back_for_ctx(data["ctx"]),
                                             await _is_cover(photo, data["ctx"])),
            )
        except Exception:
            pass
    await message.answer("✅ Подпись сохранена.")


@router.callback_query(F.data.startswith("ph:cov:"))
@admin_only
async def cb_photo_cover(call: CallbackQuery, bot: Bot):
    _, _, pid, ctx = call.data.split(":")  # type: ignore
    photo = await db.get_photo(int(pid))
    if not photo:
        await call.answer("Не найдено", show_alert=True)
        return
    if ctx.startswith("a"):
        await db.update_album(int(ctx[1:]), cover_photo_id=photo["id"])
        await call.answer("⭐ Теперь это обложка фотосета")
    elif ctx.startswith("s"):
        sid = int(ctx[1:])
        svc = await db.get_service(sid)
        new_cover = copy_upload(photo["path"])
        new_thumb = copy_upload(photo["thumb"])
        await db.update_service(sid, cover_path=new_cover, cover_thumb=new_thumb)
        if svc:
            await delete_upload_files([svc["cover_path"], svc["cover_thumb"]])
        await call.answer("⭐ Теперь это обложка услуги")
    else:
        await call.answer()
        return
    try:
        await bot.edit_message_caption(
            chat_id=call.message.chat.id, message_id=call.message.message_id,  # type: ignore
            caption=await _photo_caption(photo, ctx),
            reply_markup=kb.photo_card(photo["id"], ctx, _back_for_ctx(ctx), await _is_cover(photo, ctx)),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("ph:up:"))
@admin_only
async def cb_photo_up(call: CallbackQuery):
    _, _, pid, _ctx = call.data.split(":")  # type: ignore
    await db.move_photo(int(pid), "up")
    await call.answer("Перемещено выше")


@router.callback_query(F.data.startswith("ph:dn:"))
@admin_only
async def cb_photo_dn(call: CallbackQuery):
    _, _, pid, _ctx = call.data.split(":")  # type: ignore
    await db.move_photo(int(pid), "down")
    await call.answer("Перемещено ниже")


@router.callback_query(F.data.startswith("ph:del:"))
@admin_only
async def cb_photo_del(call: CallbackQuery, bot: Bot):
    _, _, pid, ctx = call.data.split(":")  # type: ignore
    await call.answer()
    try:
        await bot.edit_message_reply_markup(
            chat_id=call.message.chat.id, message_id=call.message.message_id,  # type: ignore
            reply_markup=kb.confirm_kb(f"ph:delok:{pid}:{ctx}", f"ph:node:{pid}:{ctx}"),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("ph:node:"))
@admin_only
async def cb_photo_node(call: CallbackQuery, bot: Bot):
    _, _, pid, ctx = call.data.split(":")  # type: ignore
    photo = await db.get_photo(int(pid))
    await call.answer()
    if photo:
        try:
            await bot.edit_message_reply_markup(
                chat_id=call.message.chat.id, message_id=call.message.message_id,  # type: ignore
                reply_markup=kb.photo_card(photo["id"], ctx, _back_for_ctx(ctx), await _is_cover(photo, ctx)),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("ph:delok:"))
@admin_only
async def cb_photo_delok(call: CallbackQuery):
    _, _, pid, ctx = call.data.split(":")  # type: ignore
    paths = await db.delete_photo(int(pid))
    await delete_upload_files(paths)
    await call.answer("Удалено")
    try:
        await call.message.delete()  # type: ignore
    except Exception:
        pass
    text, markup = await _list_text_and_kb(ctx)
    await call.message.answer(text, reply_markup=markup)  # type: ignore


# ------------------------------------------------------------ движок загрузки
def _nav_after_upload(target: str, tid: int):
    b = InlineKeyboardBuilder()
    if target == "album":
        b.button(text="🖼 К фотографиям", callback_data=f"alb:ph:{tid}")
        b.button(text="📸 К фотосету", callback_data=f"alb:view:{tid}")
    elif target in ("service", "service_cover"):
        b.button(text="💼 К услуге", callback_data=f"svc:view:{tid}")
        b.button(text="⬅️ К услугам", callback_data="svc")
    elif target == "standalone":
        b.button(text="🖼 К избранному", callback_data="sel")
    else:
        b.button(text="👤 К профилю", callback_data="pf")
    b.button(text="⬅️ В меню", callback_data="menu")
    b.adjust(1)
    return b.as_markup()


@router.message(Upload.waiting, F.photo)
@admin_only
async def msg_upload_photo(message: Message, state: FSMContext):
    assert message.bot is not None
    data = await state.get_data()
    target, tid = data.get("target"), data.get("id", 0)
    info = await save_tg_photo(message.bot, message)
    if not info:
        await message.answer("⚠️ Не получилось обработать фото, попробуйте ещё раз.")
        return
    if target == "album":
        await db.add_photo(info["file"], info["thumb"], info["file_id"], album_id=tid, width=info["w"], height=info["h"])
    elif target == "service":
        await db.add_photo(info["file"], info["thumb"], info["file_id"], service_id=tid, width=info["w"], height=info["h"])
    elif target == "standalone":
        await db.add_photo(info["file"], info["thumb"], info["file_id"], width=info["w"], height=info["h"])
    else:
        # одиночные цели (обложка/аватар/hero): храним только последнее
        for old in data.get("pending", []):
            await delete_upload_files([old["file"], old["thumb"]])
        await state.update_data(pending=[info])
    count = data.get("count", 0) + 1
    await state.update_data(count=count)
    text = f"📥 Загружено: {count}\n\nПрисылайте ещё или нажмите «✅ Готово»."
    status_id = data.get("status_msg_id")
    try:
        if status_id:
            await message.bot.edit_message_text(text, chat_id=message.chat.id, message_id=status_id)
        else:
            raise ValueError("no status")
    except Exception:
        sent = await message.answer(text)
        await state.update_data(status_msg_id=sent.message_id)


@router.message(Upload.waiting, F.text == "✅ Готово")
@admin_only
async def msg_upload_done(message: Message, state: FSMContext):
    data = await state.get_data()
    target, tid = data.get("target"), data.get("id", 0)
    count = data.get("count", 0)
    pending = data.get("pending", [])
    note = ""
    if target == "service_cover" and pending:
        svc = await db.get_service(tid)
        await db.update_service(tid, cover_path=pending[-1]["file"], cover_thumb=pending[-1]["thumb"])
        if svc:
            await delete_upload_files([svc["cover_path"], svc["cover_thumb"]])
        note = "🖼 Обложка услуги обновлена."
    elif target == "avatar" and pending:
        old = [await db.get_setting("avatar_path"), await db.get_setting("avatar_thumb")]
        await db.set_setting("avatar_path", pending[-1]["file"])
        await db.set_setting("avatar_thumb", pending[-1]["thumb"])
        await delete_upload_files(old)
        note = "🖼 Аватарка обновлена."
    elif target == "hero" and pending:
        old = [await db.get_setting("hero_path"), await db.get_setting("hero_thumb")]
        await db.set_setting("hero_path", pending[-1]["file"])
        await db.set_setting("hero_thumb", pending[-1]["thumb"])
        await delete_upload_files(old)
        note = "🌄 Фото главного экрана обновлено."
    elif target in ("album", "service", "standalone"):
        note = f"✅ Загружено фото: {count}."
    else:
        note = "Ничего не загружено."
    await state.clear()
    await message.answer(note + "\n\nИзменения уже на сайте ✨", reply_markup=ReplyKeyboardRemove())
    await message.answer("Куда дальше?", reply_markup=_nav_after_upload(target, tid))


@router.message(Upload.waiting, F.text == "❌ Отмена")
@admin_only
async def msg_upload_cancel(message: Message, state: FSMContext):
    data = await state.get_data()
    for old in data.get("pending", []):
        await delete_upload_files([old["file"], old["thumb"]])
    await state.clear()
    await message.answer("Загрузка остановлена.", reply_markup=ReplyKeyboardRemove())
    await message.answer("Куда дальше?", reply_markup=_nav_after_upload(data.get("target", ""), data.get("id", 0)))


@router.message(Upload.waiting, F.text, ~F.text.startswith("/"))
@admin_only
async def msg_upload_hint(message: Message):
    await message.answer("📥 Пришлите фото или нажмите «✅ Готово».")
