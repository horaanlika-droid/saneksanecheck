"""Точка входа: один процесс = веб-сервер (мини-приложение + API) + бот (polling).

Запуск:  python -m app.main
Хостингу нужны только переменные окружения BOT_TOKEN и ADMIN_IDS (+ WEBAPP_URL).
"""

from __future__ import annotations

import asyncio
import logging

import uvicorn

from app.config import get_settings
from app.db import init_db
from app.seed import seed_if_empty
from app.server import create_app


async def run_bot() -> None:
    from aiogram.exceptions import TelegramUnauthorizedError

    from app.bot.bot import create_bot, create_dispatcher

    try:
        bot = create_bot()
        dp = create_dispatcher()
        logging.getLogger(__name__).info("starting bot polling...")
        await dp.start_polling(bot)
    except TelegramUnauthorizedError:
        logging.getLogger(__name__).error("BOT_TOKEN невалиден — бот не запущен, сайт продолжает работать")
    except Exception:
        logging.getLogger(__name__).exception("bot crashed")


async def amain() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger(__name__)

    await init_db()
    await seed_if_empty()

    if not settings.BOT_TOKEN:
        log.warning("BOT_TOKEN не задан — запущен только сайт без бота")
    if not settings.admin_ids:
        log.warning("ADMIN_IDS пуст — добавьте свой telegram id, иначе админка бота недоступна")

    bot_task = None
    if settings.BOT_TOKEN:
        bot_task = asyncio.create_task(run_bot())

    config = uvicorn.Config(create_app(), host=settings.HOST, port=settings.PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

    if bot_task:
        bot_task.cancel()


def main() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    main()
