# -*- coding: utf-8 -*-
"""
Reply keyboards for user and admin flows.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.texts import (
    BTN_HELP,
    BTN_HISTORY,
    BTN_ADD_POST,
    BTN_TARGET_GROUP,
    BTN_ADMINS,
)


def admin_main_keyboard(include_owner: bool = False) -> ReplyKeyboardMarkup:
    """Admin: main menu. include_owner=True adds Adminlar row for owner."""
    rows = [
        [KeyboardButton(text=BTN_HISTORY), KeyboardButton(text=BTN_ADD_POST)],
        [KeyboardButton(text=BTN_TARGET_GROUP)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    if include_owner:
        rows.append([KeyboardButton(text=BTN_ADMINS)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )
