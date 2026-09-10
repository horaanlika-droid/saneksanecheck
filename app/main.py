"""Точка входа: один процесс = веб-сервер (мини-приложение + API) + бот (polling).

Запуск:  python -m app.main
Хостингу нужны только переменные окружения BOT_TOKEN и ADMIN_IDS (+ WEBAPP_URL).
"""

from __future__ import annotations

import asyncio
import logging
import time

import uvicorn

from app.config import get_settings
from app.db import init_db
from app.seed import seed_if_empty
from app.server import create_app


async def run_bot() -> None:
    """Запускает polling с автоперезапуском: сетевой сбой или временная ошибка
    Telegram не должны убивать бота навсегда (сайт при этом работает всегда)."""
    from aiogram.exceptions import TelegramUnauthorizedError

    from app.bot.bot import create_bot, create_dispatcher

    log = logging.getLogger(__name__)
    # диспетчер создаём один раз: роутеры-обработчики — модульные синглтоны,
    # повторное include_routers() бросает RuntimeError
    dp = create_dispatcher()
    delay = 5
    while True:
        bot = None
        started = time.monotonic()
        try:
            bot = create_bot()
            log.info("starting bot polling...")
            await dp.start_polling(bot)
            break  # polling завершился штатно
        except asyncio.CancelledError:
            raise
        except TelegramUnauthorizedError:
            log.error("BOT_TOKEN невалиден — бот не запущен, сайт продолжает работать")
            return
        except Exception:
            log.exception("bot crashed — перезапуск через %s c", delay)
            if bot is not None:
                try:
                    await bot.session.close()
                except Exception:
                    pass
            await asyncio.sleep(delay)
            # если polling проработал достаточно долго — это был разовый сбой,
            # начинаем с малого шага; иначе наращиваем backoff
            delay = 5 if time.monotonic() - started > 120 else min(delay * 2, 60)


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
