# -*- coding: utf-8 -*-
"""
User-facing handlers: oddiy foydalanuvchilar uchun /start va xabarlar.
Oddiy user: botga xabar yozishi mumkin, lekin bot har doim bitta tushuntiruvchi javob qaytaradi.
"""
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject, Filter

from config import is_owner
from bot.texts import (
    WELCOME,
    WELCOME_USER_ONLY_VIA_GROUP,
    USER_SIMPLE_REPLY,
)
from bot.services import user_service, admin_service
from bot.keyboards.reply import admin_main_keyboard

logger = logging.getLogger(__name__)
router = Router(name="user")


class _NotAdminOrOwnerFilter(Filter):
    """Let only non-admin, non-owner private text reach this handler; admin/owner text goes to admin router."""

    async def __call__(self, message: Message) -> bool:
        uid = message.from_user.id if message.from_user else 0
        if is_owner(uid):
            return False
        return not await admin_service.is_admin(uid)


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message, command: CommandObject = None) -> None:
    """Start with optional ?start=post_123 — user yaratiladi. Deep-link endi lead yaratmaydi."""
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    is_admin_user = await admin_service.is_admin(uid)
    if user_is_owner or is_admin_user:
        await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=user_is_owner))
    else:
        await message.answer(USER_SIMPLE_REPLY)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Regular /start in private (guruh posti orqali emas)."""
    await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    is_admin_user = await admin_service.is_admin(uid)
    if user_is_owner or is_admin_user:
        await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=user_is_owner))
    else:
        await message.answer(USER_SIMPLE_REPLY)


@router.message(
    F.chat.type == "private",
    F.text,
    ~F.text.startswith("/"),
    _NotAdminOrOwnerFilter(),
)
async def private_message_simple_reply(message: Message) -> None:
    """Oddiy user xabar yozganda: har doim bitta tushuntiruvchi javob qaytariladi."""
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    # Faqat tushuntiruvchi javob
    await message.answer(USER_SIMPLE_REPLY)
