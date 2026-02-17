# -*- coding: utf-8 -*-
"""
Reply keyboards for user and admin flows.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.texts import (
    BTN_USER_WRITE,
    BTN_HELP,
    BTN_HISTORY,
    BTN_POST_ON,
    BTN_POST_OFF,
    BTN_SCHEDULE,
    BTN_BANNER,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
    BTN_ADMINS,
)


def user_main_keyboard() -> ReplyKeyboardMarkup:
    """User: single button to send message (lead)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_USER_WRITE)],
        ],
        resize_keyboard=True,
    )


def admin_main_keyboard(include_owner: bool = False) -> ReplyKeyboardMarkup:
    """Admin: main menu. include_owner=True adds Adminlar row for owner."""
    rows = [
        [KeyboardButton(text=BTN_HELP), KeyboardButton(text=BTN_HISTORY)],
        [KeyboardButton(text=BTN_POST_ON), KeyboardButton(text=BTN_POST_OFF)],
        [KeyboardButton(text=BTN_SCHEDULE), KeyboardButton(text=BTN_BANNER)],
        [KeyboardButton(text=BTN_TARGET_GROUP), KeyboardButton(text=BTN_LEAD_GROUP)],
    ]
    if include_owner:
        rows.append([KeyboardButton(text=BTN_ADMINS)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )
