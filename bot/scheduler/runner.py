# -*- coding: utf-8 -*-
"""
Scheduler registry: add/remove cron jobs when admin adds/removes schedule times.
"""
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from aiogram import Bot

from bot.scheduler.posting import post_scheduled_content

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


def set_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Called from main after scheduler.start()."""
    global _scheduler
    _scheduler = scheduler


def get_scheduler() -> Optional[AsyncIOScheduler]:
    return _scheduler


def add_schedule_job(
    bot: Bot,
    bot_username: str,
    schedule_id: int,
    time_str: str,
) -> bool:
    """Add a cron job for the given schedule. Returns True if added."""
    s = get_scheduler()
    if not s:
        logger.warning("Scheduler not registered, cannot add job for schedule_id=%s", schedule_id)
        return False
    try:
        parts = time_str.split(":")
        hour, minute = int(parts[0]), int(parts[1])

        async def job(sid: int = schedule_id) -> None:
            await post_scheduled_content(bot, bot_username, sid)

        s.add_job(
            job,
            CronTrigger(hour=hour, minute=minute),
            id=f"post_{schedule_id}",
            replace_existing=True,
        )
        logger.info("Added scheduler job for schedule_id=%s at %s", schedule_id, time_str)
        return True
    except Exception as e:
        logger.exception("Failed to add schedule job %s: %s", schedule_id, e)
        return False


def remove_schedule_job(schedule_id: int) -> bool:
    """Remove cron job for the given schedule_id. Returns True if removed."""
    s = get_scheduler()
    if not s:
        return False
    try:
        s.remove_job(f"post_{schedule_id}")
        logger.info("Removed scheduler job for schedule_id=%s", schedule_id)
        return True
    except Exception as e:
        logger.debug("No job to remove for schedule_id=%s: %s", schedule_id, e)
        return False
