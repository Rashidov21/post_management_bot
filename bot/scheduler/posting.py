# -*- coding: utf-8 -*-
"""
Scheduled posting: run at configured times, post active content to target group.
"""
import logging
from typing import Optional

from aiogram import Bot

from bot.services import content_service, settings_service
from bot.keyboards.inline import contact_admin_keyboard_start_link

logger = logging.getLogger(__name__)


async def post_active_content_to_group(bot: Bot, bot_username: str) -> None:
    """
    Post current active content to target group with "Contact Admin" button.
    If no active content or no target group, skip. On success log to posts_log.
    """
    target_group_id = await settings_service.get_target_group_id()
    if not target_group_id:
        logger.warning("Target group not set, skipping scheduled post")
        return
    content = await content_service.get_active_content()
    if not content:
        logger.warning("No active content, skipping scheduled post")
        return
    try:
        if content.content_type == "photo" and content.file_id:
            msg = await bot.send_photo(
                chat_id=target_group_id,
                photo=content.file_id,
                caption=content.caption or "",
                reply_markup=contact_admin_keyboard_start_link(bot_username, content.id),
            )
        elif content.content_type == "video" and content.file_id:
            msg = await bot.send_video(
                chat_id=target_group_id,
                video=content.file_id,
                caption=content.caption or "",
                reply_markup=contact_admin_keyboard_start_link(bot_username, content.id),
            )
        elif content.content_type == "text" or content.text:
            text = content.text or content.caption or ""
            msg = await bot.send_message(
                chat_id=target_group_id,
                text=text,
                reply_markup=contact_admin_keyboard_start_link(bot_username, content.id),
            )
        else:
            logger.warning("Content %s has no file_id or text", content.id)
            return
        await content_service.log_post(content.id, target_group_id, msg.message_id)
        logger.info("Posted content %s to group %s", content.id, target_group_id)
    except Exception as e:
        logger.exception("Failed to post content to group: %s", e)
        raise
