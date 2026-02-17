# -*- coding: utf-8 -*-
"""
User-facing handlers: /start, private messages as leads, rate limit.
"""
import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject

from config import LEAD_RATE_LIMIT_PER_HOUR, OWNER_ID
from bot.texts import WELCOME, LEAD_SENT, LEAD_RATE_LIMIT, BTN_USER_WRITE, USER_WRITE_HINT
from bot.services import user_service, leads_service, settings_service, admin_service
from bot.keyboards.reply import user_main_keyboard, admin_main_keyboard

logger = logging.getLogger(__name__)
router = Router(name="user")

# In-memory: telegram_id -> content_id (set when user opens bot via post link)
_lead_source_by_user: dict[int, int] = {}


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message, command: CommandObject = None) -> None:
    """Start with optional ?start=post_123 for lead source."""
    await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    if command and command.args and command.args.startswith("post_"):
        try:
            _lead_source_by_user[message.from_user.id] = int(command.args.split("_", 1)[1])
        except (IndexError, ValueError):
            pass
    uid = message.from_user.id if message.from_user else 0
    is_owner = uid == OWNER_ID
    is_admin_user = await admin_service.is_admin(uid)
    if is_owner or is_admin_user:
        await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=is_owner))
    else:
        await message.answer(WELCOME, reply_markup=user_main_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Regular /start in private."""
    await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    uid = message.from_user.id if message.from_user else 0
    is_owner = uid == OWNER_ID
    is_admin_user = await admin_service.is_admin(uid)
    if is_owner or is_admin_user:
        await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=is_owner))
    else:
        await message.answer(WELCOME, reply_markup=user_main_keyboard())


@router.message(F.chat.type == "private", F.text == BTN_USER_WRITE)
async def btn_user_write(message: Message) -> None:
    """User pressed 'Xabar yuborish' — show hint."""
    await message.answer(USER_WRITE_HINT)


@router.message(F.chat.type == "private", F.text, ~F.text.startswith("/"))
async def private_message_as_lead(message: Message) -> None:
    """
    Non-command text in private is forwarded to admin group as lead (with rate limit).
    Commands (starting with /) go to admin/owner routers. Owner/admin messages are not forwarded as leads.
    """
    uid = message.from_user.id if message.from_user else 0
    if uid == OWNER_ID or await admin_service.is_admin(uid):
        return  # Let admin/owner use commands; their plain text is not treated as lead
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    # Rate limit
    since = datetime.utcnow() - timedelta(hours=1)
    count = await leads_service.count_leads_from_user_since(message.from_user.id, since)
    if count >= LEAD_RATE_LIMIT_PER_HOUR:
        await message.answer(LEAD_RATE_LIMIT)
        return
    source_content_id = _lead_source_by_user.pop(message.from_user.id, None)
    admin_group_id = await settings_service.get_admin_group_id()
    if not admin_group_id:
        await leads_service.create_lead(
            user_id=user.id,
            telegram_user_id=message.from_user.id,
            message_text=message.text or "",
            source_content_id=source_content_id,
        )
        await message.answer(LEAD_SENT)
        return
    lead = await leads_service.create_lead(
        user_id=user.id,
        telegram_user_id=message.from_user.id,
        message_text=message.text or "",
        source_content_id=source_content_id,
    )
    from bot.texts import LEAD_FORWARD_TEMPLATE, LEAD_SOURCE_UNKNOWN
    from bot.keyboards.inline import take_lead_keyboard

    name = message.from_user.full_name or "—"
    username = message.from_user.username or "—"
    source_str = f"#{source_content_id}" if source_content_id else LEAD_SOURCE_UNKNOWN
    forward_text = LEAD_FORWARD_TEMPLATE.format(
        name=name,
        username=username,
        user_id=message.from_user.id,
        text=(message.text or "")[:500],
        source=source_str,
    )
    try:
        await message.bot.send_message(
            chat_id=admin_group_id,
            text=forward_text,
            reply_markup=take_lead_keyboard(lead.id),
        )
    except Exception as e:
        logger.exception("Failed to forward lead to admin group: %s", e)
    await message.answer(LEAD_SENT)
