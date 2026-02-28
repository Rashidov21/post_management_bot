# -*- coding: utf-8 -*-
"""
Reply keyboards for user and admin flows.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.texts import (
    BTN_HELP,
    BTN_HISTORY,
    BTN_ADD_POST,
    BTN_ADD_TEXT_POST,
    BTN_TARGET_GROUP,
)


def admin_main_keyboard(include_owner: bool = False) -> ReplyKeyboardMarkup:
    """Admin/Owner: main menu. Hamma uchun bir xil tugmalar."""
    rows = [
        [KeyboardButton(text=BTN_HISTORY), KeyboardButton(text=BTN_ADD_POST)],
        [KeyboardButton(text=BTN_ADD_TEXT_POST)],
        [KeyboardButton(text=BTN_TARGET_GROUP)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )
