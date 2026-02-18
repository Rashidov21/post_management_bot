# -*- coding: utf-8 -*-
"""
Owner-only handlers: /add_admin, /remove_admin, /list_admins.
"""
import logging

from aiogram import Router, F
from aiogram.types import Message

from bot.texts import (
    REPLY_TO_ADD_ADMIN,
    REPLY_TO_REMOVE_ADMIN,
    ADMIN_ADDED,
    ADMIN_REMOVED,
    ADMIN_ALREADY,
    ADMIN_NOT_FOUND,
    LIST_ADMINS_HEADER,
)
from bot.services import admin_service
from bot.texts import BTN_ADMINS
from bot.keyboards.reply import admin_main_keyboard
from bot.keyboards.inline import owner_admins_keyboard
from config import is_owner

logger = logging.getLogger(__name__)
router = Router(name="owner")


def _owner_kb(message: Message):
    return admin_main_keyboard(include_owner=True)


@router.message(F.chat.type == "private", F.text == BTN_ADMINS)
async def btn_admins(message: Message) -> None:
    """Owner: show admin management inline menu."""
    if not is_owner(message.from_user.id):
        return
    await message.answer("Adminlar boshqaruvi:", reply_markup=owner_admins_keyboard())


@router.message(F.chat.type == "private", F.text == "/add_admin")
async def cmd_add_admin(message: Message) -> None:
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer(REPLY_TO_ADD_ADMIN)
        return
    user = message.reply_to_message.from_user
    if await admin_service.is_admin(user.id):
        await message.answer(ADMIN_ALREADY)
        return
    ok = await admin_service.add_admin(user.id, user.username)
    await message.answer(ADMIN_ADDED if ok else "Xatolik yuz berdi.", reply_markup=_owner_kb(message))


@router.message(F.chat.type == "private", F.text == "/remove_admin")
async def cmd_remove_admin(message: Message) -> None:
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.answer(REPLY_TO_REMOVE_ADMIN)
        return
    user = message.reply_to_message.from_user
    ok = await admin_service.remove_admin(user.id)
    await message.answer(ADMIN_REMOVED if ok else ADMIN_NOT_FOUND, reply_markup=_owner_kb(message))


@router.message(F.chat.type == "private", F.text == "/list_admins")
async def cmd_list_admins(message: Message) -> None:
    admins = await admin_service.list_admins()
    if not admins:
        await message.answer(LIST_ADMINS_HEADER + "\n(bo'sh)", reply_markup=_owner_kb(message))
        return
    lines = [LIST_ADMINS_HEADER]
    for a in admins:
        uname = f"@{a.username}" if a.username else ""
        lines.append(f"- {a.telegram_id} {uname}")
    await message.answer("\n".join(lines), reply_markup=_owner_kb(message))
