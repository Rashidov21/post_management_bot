# -*- coding: utf-8 -*-
"""
User-facing handlers: oddiy foydalanuvchilar uchun /start va xabarlar.
Oddiy user: botga xabar yozishi mumkin, lekin bot har doim bitta tushuntiruvchi javob qaytaradi.
Admin/owner: matn yuborganda matnli post qo'shish (birinchisi user routerda ushlanadi).
"""
import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject, Filter

from config import is_owner
from bot.texts import (
    WELCOME,
    USER_SIMPLE_REPLY,
)
from bot.services import admin_service
from bot.keyboards.reply import admin_main_keyboard

# Admin modulidan matnli post logikasi (user router birinchi bo‘lib admin/owner matnni ushlashi uchun)
from bot.handlers import admin as admin_handlers

logger = logging.getLogger(__name__)
router = Router(name="user")


class _IsAdminOrOwnerFilter(Filter):
    """True when user is owner or admin (matnli postni user routerda ushlash uchun)."""

    async def __call__(self, message: Message) -> bool:
        uid = message.from_user.id if message.from_user else 0
        if is_owner(uid):
            return True
        return await admin_service.is_admin(uid)


class _NotAdminOrOwnerFilter(Filter):
    """Let only non-admin, non-owner private text reach this handler; admin/owner text goes to admin router."""

    async def __call__(self, message: Message) -> bool:
        uid = message.from_user.id if message.from_user else 0
        if is_owner(uid):
            return False
        return not await admin_service.is_admin(uid)


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message, command: CommandObject = None) -> None:
    """Start with optional ?start=post_123. Oddiy user uchun faqat tushuntiruvchi javob."""
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
    F.text.filter(lambda t: t not in admin_handlers._ADMIN_BUTTON_TEXTS),
    _IsAdminOrOwnerFilter(),
)
async def admin_owner_text_post(message: Message) -> None:
    """Admin/owner matn yuborganda — matnli post qo'shish (user routerda birinchi ushlanadi)."""
    await admin_handlers.handle_admin_text_post(message)


@router.message(
    F.chat.type == "private",
    F.text,
    ~F.text.startswith("/"),
    _NotAdminOrOwnerFilter(),
)
async def private_message_simple_reply(message: Message) -> None:
    """Oddiy user xabar yozganda: har doim bitta tushuntiruvchi javob qaytariladi."""
    await message.answer(USER_SIMPLE_REPLY)
