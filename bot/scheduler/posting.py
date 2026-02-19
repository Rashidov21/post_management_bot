# -*- coding: utf-8 -*-
"""
Scheduled posting: at each schedule time, post the content assigned to that time.
"""
import logging

from aiogram import Bot

from bot.services import content_service, settings_service, schedule_service
from bot.keyboards.inline import contact_bot_for_post_keyboard

logger = logging.getLogger(__name__)


async def post_scheduled_content(bot: Bot, bot_username: str, schedule_id: int) -> None:
    """
    At this schedule time: post the content assigned to this schedule_id.
    If no content assigned, or posting disabled, or content publishing_enabled=0, skip.
    """
    if not await settings_service.is_posting_enabled():
        return
    target_group_id = await settings_service.get_target_group_id()
    if not target_group_id:
        logger.warning("Target group not set, skipping scheduled post")
        return
    content_id = await schedule_service.get_content_id_for_schedule(schedule_id)
    if not content_id:
        logger.debug("No content assigned to schedule_id=%s", schedule_id)
        return
    content = await content_service.get_content_by_id(content_id)
    # Skip if content missing, deleted, or publishing disabled
    if not content or content.status != "active" or not content.publishing_enabled:
        return
    ok = await post_content_by_id_to_group(bot, bot_username, content_id)
    if ok:
        logger.info("Scheduled post: content %s at schedule_id %s", content_id, schedule_id)


async def post_content_by_id_to_group(bot: Bot, bot_username: str, content_id: int) -> bool:
    """
    Post a specific content (by id) to target group immediately. Does not change active content.
    Returns True if posted, False if no group, no content, or content has no media/text.
    """
    target_group_id = await settings_service.get_target_group_id()
    if not target_group_id:
        logger.warning("Target group not set, skipping post now")
        return False
    content = await content_service.get_content_by_id(content_id)
    if not content or content.status != "active" or not content.publishing_enabled:
        return False
    try:
        markup = contact_bot_for_post_keyboard(bot_username, content_id)
        if content.content_type == "photo" and content.file_id:
            msg = await bot.send_photo(
                chat_id=target_group_id,
                photo=content.file_id,
                caption=content.caption or "",
                reply_markup=markup,
            )
        elif content.content_type == "video" and content.file_id:
            msg = await bot.send_video(
                chat_id=target_group_id,
                video=content.file_id,
                caption=content.caption or "",
                reply_markup=markup,
            )
        elif content.content_type == "text" or content.text:
            text = (content.text or content.caption or "").strip()
            if not text:
                return False
            msg = await bot.send_message(
                chat_id=target_group_id,
                text=text,
                reply_markup=markup,
            )
        else:
            return False
        await content_service.log_post(content.id, target_group_id, msg.message_id)
        logger.info("Posted content %s to group %s (post now)", content.id, target_group_id)
        return True
    except Exception as e:
        logger.exception("Failed to post content %s to group: %s", content_id, e)
        return False
