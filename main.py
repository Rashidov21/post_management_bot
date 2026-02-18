# -*- coding: utf-8 -*-
"""
Post Management Bot — entry point.
Scheduler, routers, DB init and graceful shutdown.
"""
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from config import BOT_TOKEN, LOG_LEVEL, LOG_FORMAT, SCHEDULER_TIMEZONE, validate_config
from bot.database import init_db, open_app_connection, close_app_connection
from bot.scheduler.posting import post_scheduled_content
from bot.services import schedule_service, settings_service
from bot.handlers import user, admin, owner
from bot.middlewares.admin import AdminOnlyMiddleware, OwnerOnlyMiddleware


def setup_logging() -> None:
    """Configure root logger and optional file handler."""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    try:
        fh = RotatingFileHandler(
            "bot.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(fh)
    except Exception:
        pass


async def setup_scheduler(bot: Bot, bot_username: str) -> AsyncIOScheduler:
    """Load schedules from DB and add cron jobs; each time posts its assigned content."""
    scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)

    schedules = await schedule_service.list_schedules()
    for s in schedules:
        if not s.enabled:
            continue
        parts = s.time_str.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        schedule_id = s.id

        async def job(sid: int = schedule_id) -> None:
            await post_scheduled_content(bot, bot_username, sid)

        scheduler.add_job(
            job,
            CronTrigger(hour=hour, minute=minute),
            id=f"post_{s.id}",
            replace_existing=True,
        )

    scheduler.start()
    return scheduler


async def main() -> None:
    validate_config()
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Post Management Bot")

    await init_db()
    await open_app_connection()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(user.router)
    admin.router.message.middleware(AdminOnlyMiddleware())
    admin.router.callback_query.middleware(AdminOnlyMiddleware())
    dp.include_router(admin.router)
    owner.router.message.middleware(OwnerOnlyMiddleware())
    dp.include_router(owner.router)

    @dp.error()
    async def global_error_handler(event: ErrorEvent) -> None:
        logger.exception("Handler error: %s", event.exception, exc_info=True)
        try:
            update = event.update
            if update.message:
                await update.message.answer(
                    "Xatolik yuz berdi. Iltimos keyinroq urinib ko'ring."
                )
            elif update.callback_query:
                await update.callback_query.answer(
                    "Xatolik yuz berdi.", show_alert=True
                )
        except Exception:
            pass

    me = await bot.get_me()
    bot_username = me.username or ""

    scheduler = await setup_scheduler(bot, bot_username)

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await close_app_connection()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
