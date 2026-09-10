"""Команды /start, /app и главное меню админки."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import db
from app.bot import keyboards as kb
from app.bot.common import admin_only, safe_edit, webapp_url

router = Router()


async def get_counts() -> dict:
    cats = await db.list_categories()
    albums = await db.list_albums()
    return {
        "categories": len(cats),
        "albums": len(albums),
        "standalone": len(await db.list_photos(standalone=True)),
        "services": len(await db.list_services()),
        "exhibitions": len(await db.list_exhibitions()),
        "new_leads": await db.count_new_leads(),
        "photos": await db.count_photos(),
    }


def panel_text(counts: dict, brand: str) -> str:
    return (
        f"⚙️ <b>Админ-панель — {brand}</b>\n\n"
        f"🗂 Разделов: {counts['categories']} · 📸 Фотосетов: {counts['albums']} · 🖼 Фото: {counts['photos']}\n"
        f"💼 Услуг: {counts['services']} · 🏆 Выставок: {counts['exhibitions']}\n"
        f"💬 Новых заявок: {counts['new_leads']}\n\n"
        "Выберите раздел:"
    )


async def show_panel(message: Message) -> None:
    counts = await get_counts()
    brand = await db.get_setting("brand_name", "Photographer")
    await safe_edit(message, panel_text(counts, brand), kb.main_menu(counts))


async def app_button_kb() -> InlineKeyboardMarkup | None:
    url = await webapp_url()
    if not url:
        return None
    b = InlineKeyboardBuilder()
    b.button(text="📷 Открыть портфолио", web_app=WebAppInfo(url=url))
    return b.as_markup()


@router.message(CommandStart())
async def cmd_start(message: Message):
    if await db.is_admin(message.from_user.id if message.from_user else 0):
        counts = await get_counts()
        brand = await db.get_setting("brand_name", "Photographer")
        await message.answer(panel_text(counts, brand), reply_markup=kb.main_menu(counts))
        return
    brand = await db.get_setting("brand_name", "Photographer")
    tagline = await db.get_setting("tagline", "")
    city = await db.get_setting("city", "")
    markup = await app_button_kb()
    text = f"Привет! Это официальный бот <b>{brand}</b> 📷\n"
    if tagline:
        text += f"<i>{tagline}</i>\n"
    if city:
        text += f"📍 {city}\n"
    text += "\nОткройте приложение, чтобы посмотреть работы, услуги и записаться на съёмку."
    if markup is None:
        text += "\n\n<i>Приложение скоро будет доступно.</i>"
    await message.answer(text, reply_markup=markup)


@router.message(Command("app"))
async def cmd_app(message: Message):
    markup = await app_button_kb()
    if markup is None:
        if message.from_user and await db.is_admin(message.from_user.id):
            await message.answer(
                "🔗 Адрес приложения не задан. Откройте сайт один раз с хостинга — "
                "адрес определится автоматически, либо укажите WEBAPP_URL в настройках "
                "хостинга / в разделе «Профиль» → «Адрес веб-приложения»."
            )
        else:
            await message.answer("Приложение скоро будет доступно ✨")
        return
    await message.answer("📷 Портфолио — нажмите кнопку ниже:", reply_markup=markup)


@router.message(Command("admin"))
@admin_only
async def cmd_admin(message: Message):
    counts = await get_counts()
    brand = await db.get_setting("brand_name", "Photographer")
    await message.answer(panel_text(counts, brand), reply_markup=kb.main_menu(counts))


@router.callback_query(F.data == "menu")
@admin_only
async def cb_menu(call: CallbackQuery):
    await call.answer()
    if isinstance(call.message, Message):
        await show_panel(call.message)


@router.callback_query(F.data == "openapp")
@admin_only
async def cb_openapp(call: CallbackQuery):
    markup = await app_button_kb()
    await call.answer()
    if markup is None:
        await call.message.answer("🔗 Адрес приложения не задан (WEBAPP_URL).")  # type: ignore
    else:
        await call.message.answer("📷 Портфолио:", reply_markup=markup)  # type: ignore
