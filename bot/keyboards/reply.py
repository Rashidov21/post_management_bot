# -*- coding: utf-8 -*-
"""
Reply keyboards for user and admin flows.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.texts import (
    BTN_USER_WRITE,
    BTN_USER_ADMINS,
    BTN_HELP,
    BTN_HISTORY,
    BTN_ADD_POST,
    BTN_POST_ON,
    BTN_POST_OFF,
    BTN_SCHEDULE,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
    BTN_ADMINS,
)


def user_main_keyboard() -> ReplyKeyboardMarkup:
    """User: send message (lead) and admin list."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_USER_WRITE), KeyboardButton(text=BTN_USER_ADMINS)],
        ],
        resize_keyboard=True,
    )


def admin_main_keyboard(include_owner: bool = False) -> ReplyKeyboardMarkup:
    """Admin: main menu. include_owner=True adds Adminlar row for owner."""
    rows = [
        [KeyboardButton(text=BTN_HISTORY), KeyboardButton(text=BTN_ADD_POST)],
        [KeyboardButton(text=BTN_POST_ON), KeyboardButton(text=BTN_POST_OFF)],
        [KeyboardButton(text=BTN_SCHEDULE)],
        [KeyboardButton(text=BTN_TARGET_GROUP), KeyboardButton(text=BTN_LEAD_GROUP)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    if include_owner:
        rows.append([KeyboardButton(text=BTN_ADMINS)])
    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
    )
