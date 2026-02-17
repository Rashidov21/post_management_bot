# -*- coding: utf-8 -*-
"""
Inline keyboards for user and admin flows.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts import (
    CONTACT_ADMIN_BUTTON,
    TAKE_LEAD,
    BTN_ADMIN_LIST,
    BTN_ADMIN_ADD_HINT,
    BTN_ADMIN_REMOVE_HINT,
    BTN_REFRESH_HISTORY,
)


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


def history_refresh_keyboard() -> InlineKeyboardMarkup:
    """Under history list: refresh button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_REFRESH_HISTORY, callback_data="refresh_history")],
    ])


def history_actions_keyboard(posts: list) -> InlineKeyboardMarkup:
    """Per-post actions: O'chirish (active) or Aktivlashtirish (deleted), plus refresh."""
    rows = []
    for p in posts:
        if getattr(p, "status", None) == "active":
            rows.append([InlineKeyboardButton(text="O'chirish", callback_data=f"del_post_{p.id}")])
        else:
            rows.append([InlineKeyboardButton(text="Aktivlashtirish", callback_data=f"activate_post_{p.id}")])
    rows.append([InlineKeyboardButton(text=BTN_REFRESH_HISTORY, callback_data="refresh_history")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def owner_admins_keyboard() -> InlineKeyboardMarkup:
    """Owner: admin management inline menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_ADMIN_LIST, callback_data="admin_list")],
        [
            InlineKeyboardButton(text=BTN_ADMIN_ADD_HINT, callback_data="admin_help_add"),
            InlineKeyboardButton(text=BTN_ADMIN_REMOVE_HINT, callback_data="admin_help_remove"),
        ],
    ])
