# -*- coding: utf-8 -*-
"""
Inline keyboards for user and admin flows.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts import (
    BTN_ADMIN_LIST,
    BTN_ADMIN_ADD_HINT,
    BTN_ADMIN_REMOVE_HINT,
    BTN_REFRESH_HISTORY,
    BTN_HISTORY_BACK,
    BTN_INLINE_HISTORY,
    BTN_CONFIRM_TARGET_GROUP,
    BTN_POST_CONFIRM,
    BTN_POST_CANCEL,
    POST_NOT_ASSIGNED,
    BTN_PUBLISHING_ON,
    BTN_PUBLISHING_OFF,
    BTN_NAV_HOME,
)


def history_delete_keyboard(content_id: int) -> InlineKeyboardMarkup:
    """Under history item: delete post button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'chirish", callback_data=f"del_post_{content_id}")],
    ])


def history_refresh_keyboard() -> InlineKeyboardMarkup:
    """Under history: Yangilash va Bosh menyu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_REFRESH_HISTORY, callback_data="refresh_history"),
            InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home"),
        ],
    ])


def schedule_keyboard(schedules: list) -> InlineKeyboardMarkup:
    """Backward-compat shim (no dedicated schedule menu in new flow)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home")],
    ])


def confirm_target_group_keyboard() -> InlineKeyboardMarkup:
    """After target group ID entered: Guruhni belgilash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CONFIRM_TARGET_GROUP, callback_data="confirm_target_group")],
    ])


def post_add_confirm_keyboard() -> InlineKeyboardMarkup:
    """Post qo'shish: Yakunlash va Bekor qilish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_POST_CONFIRM, callback_data="confirm_post_add"),
            InlineKeyboardButton(text=BTN_POST_CANCEL, callback_data="cancel_post_add"),
        ],
    ])


def post_add_schedule_hour_keyboard() -> InlineKeyboardMarkup:
    """Post qo'shish: nashr soati — post_time_h_0 … post_time_h_23."""
    rows = []
    for h in range(24):
        btn = InlineKeyboardButton(text=f"{h:02d}", callback_data=f"post_time_h_{h}")
        if not rows or len(rows[-1]) >= 6:
            rows.append([btn])
        else:
            rows[-1].append(btn)
    rows.append([InlineKeyboardButton(text=BTN_POST_CANCEL, callback_data="post_time_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def post_add_schedule_minute_keyboard() -> InlineKeyboardMarkup:
    """Post qo'shish: nashr minutlari 00–59 — post_time_m_00 … post_time_m_59 (6 tugma qatorda)."""
    minutes = [f"{m:02d}" for m in range(60)]
    rows = []
    for i in range(0, 60, 6):
        row = [InlineKeyboardButton(text=m, callback_data=f"post_time_m_{m}") for m in minutes[i : i + 6]]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_main_inline_keyboard() -> InlineKeyboardMarkup:
    """Admin/Owner: asosiy amallar — faqat Postlar tarixi."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_INLINE_HISTORY, callback_data="inline_history"),
        ],
        [
            InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home"),
        ],
    ])


def owner_admin_list_keyboard(admins: list) -> InlineKeyboardMarkup:
    """
    Owner: admin ro'yxati — har bir admin uchun Chat (username bo'lsa) va O'chirish.
    """
    rows = []
    for a in admins:
        tid = getattr(a, "telegram_id", a) if hasattr(a, "telegram_id") else a
        uname = getattr(a, "username", None)
        buttons = []
        if uname:
            buttons.append(InlineKeyboardButton(text="Chat", url=f"https://t.me/{uname}"))
        buttons.append(InlineKeyboardButton(text="O'chirish", callback_data=f"remove_admin_{tid}"))
        rows.append(buttons)
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
