"""Создание бота и диспетчера, автопуш настроек при старте."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    BotCommand,
    MenuButtonWebApp,
    WebAppInfo,
)

from app import db
from app.bot.notify import set_bot
from app.config import get_settings

log = logging.getLogger(__name__)


async def push_bot_settings(bot: Bot) -> None:
    """Автоматически пушит команды, описания и кнопку меню при каждом старте.
    Вручную ничего настраивать через BotFather не нужно."""
    settings = get_settings()
    brand = await db.get_setting("brand_name", "Photographer")

    try:
        await bot.set_my_commands([
            BotCommand(command="start", description="Начать"),
            BotCommand(command="app", description="📷 Открыть портфолио"),
            BotCommand(command="admin", description="⚙️ Админ-панель"),
            BotCommand(command="leads", description="💬 Новые заявки"),
            BotCommand(command="backup", description="💾 Бэкап базы и фото"),
            BotCommand(command="cancel", description="Отмена текущего действия"),
        ])
    except Exception:
        log.exception("set_my_commands failed")

    try:
        webapp_url = settings.WEBAPP_URL or await db.get_setting("webapp_url", "")
        if webapp_url:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="📷 Открыть портфолио",
                    web_app=WebAppInfo(url=webapp_url),
                )
            )
            log.info("menu button -> %s", webapp_url)
        else:
            log.warning(
                "WEBAPP_URL не задан — кнопка меню не установлена; "
                "адрес определится автоматически после первого внешнего запроса к сайту"
            )
    except Exception:
        log.exception("set_chat_menu_button failed")

    try:
        await bot.set_my_description(
            f"Официальный бот {brand} — портфолио, услуги и запись на съёмку. "
            "Нажмите кнопку меню, чтобы открыть приложение."
        )
        await bot.set_my_short_description(f"Портфолио и запись на съёмку — {brand}")
    except Exception:
        log.exception("set description failed")

    try:
        me = await bot.get_me()
        log.info("bot started as @%s", me.username)
    except Exception:
        # сетевой сбой не должен ронять startup (иначе polling не стартует)
        log.exception("get_me failed")


def create_dispatcher() -> Dispatcher:
    from app.bot.handlers import (
        albums,
        booking_leads,
        categories,
        misc,
        photos,
        profile,
        services,
        exhibitions,
        start,
    )

    dp = Dispatcher()
    dp.include_routers(
        start.router,
        profile.router,
        categories.router,
        albums.router,
        photos.router,
        services.router,
        exhibitions.router,
        booking_leads.router,
        misc.router,
    )

    async def on_startup(bot: Bot) -> None:
        set_bot(bot)
        await push_bot_settings(bot)

    async def on_shutdown(bot: Bot) -> None:
        set_bot(None)
        await bot.session.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    return dp


def create_bot() -> Bot:
    token = get_settings().BOT_TOKEN
    return Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
