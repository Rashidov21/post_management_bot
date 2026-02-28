# -*- coding: utf-8 -*-
"""
Inline keyboards for user and admin flows.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts import (
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


def schedule_hour_keyboard() -> InlineKeyboardMarkup:
    """Schedule: soat tanlash — sch_h_0 … sch_h_23."""
    rows = []
    for h in range(24):
        btn = InlineKeyboardButton(text=f"{h:02d}", callback_data=f"sch_h_{h}")
        if not rows or len(rows[-1]) >= 6:
            rows.append([btn])
        else:
            rows[-1].append(btn)
    rows.append([InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="schedule_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_minute_keyboard() -> InlineKeyboardMarkup:
    """Schedule: minut tanlash — sch_m_00 … sch_m_59."""
    minutes = [f"{m:02d}" for m in range(60)]
    rows = []
    for i in range(0, 60, 6):
        row = [InlineKeyboardButton(text=m, callback_data=f"sch_m_{m}") for m in minutes[i : i + 6]]
        rows.append(row)
    rows.append([InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="schedule_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_pick_post_keyboard(schedule_id: int, posts: list) -> InlineKeyboardMarkup:
    """Schedule uchun post tanlash — assign_schedule_{schedule_id}_content_{content_id}."""
    rows = []
    for p in posts:
        pid = getattr(p, "id", p)
        preview = (getattr(p, "caption", None) or getattr(p, "text", None) or f"#{pid}").strip() or f"Post #{pid}"
        if len(preview) > 35:
            preview = preview[:32] + "…"
        rows.append([
            InlineKeyboardButton(
                text=preview,
                callback_data=f"assign_schedule_{schedule_id}_content_{pid}",
            )
        ])
    rows.append([InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="schedule_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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


def text_post_confirm_keyboard() -> InlineKeyboardMarkup:
    """Matnli post qo'shish: Yakunlash va Bekor qilish (alohida callback_data)."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_POST_CONFIRM, callback_data="confirm_text_post_add"),
            InlineKeyboardButton(text=BTN_POST_CANCEL, callback_data="cancel_text_post_add"),
        ],
    ])


def text_post_schedule_hour_keyboard() -> InlineKeyboardMarkup:
    """Matnli post: nashr soati — text_post_h_0 … text_post_h_23."""
    rows = []
    for h in range(24):
        btn = InlineKeyboardButton(text=f"{h:02d}", callback_data=f"text_post_h_{h}")
        if not rows or len(rows[-1]) >= 6:
            rows.append([btn])
        else:
            rows[-1].append(btn)
    rows.append([InlineKeyboardButton(text=BTN_POST_CANCEL, callback_data="text_post_time_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def text_post_schedule_minute_keyboard() -> InlineKeyboardMarkup:
    """Matnli post: minutlar — text_post_m_00 … text_post_m_59."""
    minutes = [f"{m:02d}" for m in range(60)]
    rows = []
    for i in range(0, 60, 6):
        row = [InlineKeyboardButton(text=m, callback_data=f"text_post_m_{m}") for m in minutes[i : i + 6]]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_main_inline_keyboard() -> InlineKeyboardMarkup:
    """Admin/Owner: Yordam va Bosh menyu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home")],
    ])
