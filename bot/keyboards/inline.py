# -*- coding: utf-8 -*-
"""
Inline keyboards for user and admin flows.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts import CONTACT_ADMIN, TAKE_LEAD, CONTACT_ADMIN_BUTTON


def contact_admin_keyboard(post_id: int | None = None) -> InlineKeyboardMarkup:
    """Single button: Contact Admin. Optional post_id for lead source."""
    payload = str(post_id) if post_id is not None else ""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=CONTACT_ADMIN_BUTTON, url=f"https://t.me/placeholder_bot")],
    ])


def contact_admin_keyboard_start_link(bot_username: str, post_id: int | None = None) -> InlineKeyboardMarkup:
    """Contact Admin button that opens bot (start with optional start_param for post_id)."""
    url = f"https://t.me/{bot_username}"
    if post_id is not None:
        url += f"?start=post_{post_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=CONTACT_ADMIN_BUTTON, url=url)],
    ])


def take_lead_keyboard(lead_id: int) -> InlineKeyboardMarkup:
    """For admin group: Take Lead button with callback data."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TAKE_LEAD, callback_data=f"take_lead_{lead_id}")],
    ])


def history_delete_keyboard(content_id: int) -> InlineKeyboardMarkup:
    """Under history item: delete post button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'chirish", callback_data=f"del_post_{content_id}")],
    ])
