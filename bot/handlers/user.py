# -*- coding: utf-8 -*-
"""
User-facing handlers: oddiy foydalanuvchilar uchun /start va xabarlar.
Oddiy user: botga xabar yozishi mumkin, lekin bot har doim bitta tushuntiruvchi javob qaytaradi.
Admin/owner: matn yuborganda matnli post qo'shish — bitta handler ichida tekshiriladi.
"""
import logging

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject

from config import is_owner
from bot.texts import (
    WELCOME,
    USER_SIMPLE_REPLY,
    BTN_HELP,
    BTN_ADD_POST,
    BTN_ADD_TEXT_POST,
    BTN_TARGET_GROUP,
)
from bot.services import admin_service
from bot.keyboards.reply import admin_main_keyboard

from bot.handlers import admin as admin_handlers

logger = logging.getLogger(__name__)
router = Router(name="user")

# Standart tugma matnlari — bular post flow'ga tushmasin, boshqa handlerga qoladi
STANDARD_BUTTON_TEXTS = frozenset({BTN_HELP, BTN_ADD_POST, BTN_ADD_TEXT_POST, BTN_TARGET_GROUP})


async def _handle_admin_start(message: Message) -> None:
    """Admin/Owner /start: xush kelibsiz + barcha mavjud postlar (O'chirish tugmalari bilan)."""
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=user_is_owner))
    await admin_handlers.send_all_posts_to_admin(message.bot, message.chat.id, uid)


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message, command: CommandObject = None) -> None:
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    is_admin_user = await admin_service.is_admin(uid)
    if user_is_owner or is_admin_user:
        await _handle_admin_start(message)
    else:
        await message.answer(USER_SIMPLE_REPLY)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    is_admin_user = await admin_service.is_admin(uid)
    if user_is_owner or is_admin_user:
        await _handle_admin_start(message)
    else:
        await message.answer(USER_SIMPLE_REPLY)


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_(STANDARD_BUTTON_TEXTS),
)
@router.edited_message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    ~F.text.startswith("/"),
    ~F.text.in_(STANDARD_BUTTON_TEXTS),
)
async def private_text_message(message: Message) -> None:
    """Barcha private matn (standart tugma matnlari emas): admin/owner → post flow, oddiy user → USER_SIMPLE_REPLY."""
    if not message.from_user:
        return
    uid = message.from_user.id
    if is_owner(uid) or await admin_service.is_admin(uid):
        await admin_handlers.handle_admin_text_post(message)
    else:
        await message.answer(USER_SIMPLE_REPLY)
