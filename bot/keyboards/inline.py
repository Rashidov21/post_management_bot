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
    BTN_ADD_TIME,
    BTN_POST_NOW,
    BTN_HISTORY_BACK,
    BTN_INLINE_HISTORY,
    BTN_INLINE_SCHEDULE,
    BTN_INLINE_POST_ON,
    BTN_INLINE_POST_OFF,
    BTN_SAVE_AS_BANNER,
    BTN_SET_BOT_PIC,
    BTN_CONFIRM_TARGET_GROUP,
    BTN_CONFIRM_ADMIN_GROUP,
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


def history_list_keyboard(posts: list) -> InlineKeyboardMarkup:
    """Postlar ro'yxati: har bir post uchun 'Tanlash' (history_show_{id}), oxirida Yangilash."""
    rows = []
    for p in posts:
        label = f"ID: {p.id} | {p.content_type} | {_short_date(p)}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"history_show_{p.id}")])
    rows.append([InlineKeyboardButton(text=BTN_REFRESH_HISTORY, callback_data="refresh_history")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _short_date(p) -> str:
    """Short created_at for list button label (callback_data 64 byte limit)."""
    ca = getattr(p, "created_at", None)
    if ca is None:
        return ""
    if hasattr(ca, "strftime"):
        return ca.strftime("%d.%m.%y")
    return str(ca)[:10]


def history_single_keyboard(post) -> InlineKeyboardMarkup:
    """Bitta post uchun: O'chirish/Aktivlashtirish, Hozir joylash, Orqaga."""
    rows = []
    if getattr(post, "status", None) == "active":
        rows.append([
            InlineKeyboardButton(text="O'chirish", callback_data=f"del_post_{post.id}"),
            InlineKeyboardButton(text=BTN_POST_NOW, callback_data=f"post_now_{post.id}"),
        ])
    else:
        rows.append([
            InlineKeyboardButton(text="Aktivlashtirish", callback_data=f"activate_post_{post.id}"),
            InlineKeyboardButton(text=BTN_POST_NOW, callback_data=f"post_now_{post.id}"),
        ])
    rows.append([InlineKeyboardButton(text=BTN_HISTORY_BACK, callback_data="history_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def history_actions_keyboard(posts: list) -> InlineKeyboardMarkup:
    """Per-post actions: O'chirish/Aktivlashtirish, Hozir joylash; plus refresh."""
    rows = []
    for p in posts:
        if getattr(p, "status", None) == "active":
            rows.append([
                InlineKeyboardButton(text="O'chirish", callback_data=f"del_post_{p.id}"),
                InlineKeyboardButton(text=BTN_POST_NOW, callback_data=f"post_now_{p.id}"),
            ])
        else:
            rows.append([
                InlineKeyboardButton(text="Aktivlashtirish", callback_data=f"activate_post_{p.id}"),
                InlineKeyboardButton(text=BTN_POST_NOW, callback_data=f"post_now_{p.id}"),
            ])
    rows.append([InlineKeyboardButton(text=BTN_REFRESH_HISTORY, callback_data="refresh_history")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_keyboard(schedules: list) -> InlineKeyboardMarkup:
    """Nashr vaqtlari: har bir vaqt uchun O'chirish, oxirida Vaqt qo'shish."""
    rows = []
    for s in schedules:
        time_str = getattr(s, "time_str", str(s))
        cb = "del_time_" + time_str.replace(":", "_")
        rows.append([InlineKeyboardButton(text=f"{time_str}  |  O'chirish", callback_data=cb)])
    rows.append([InlineKeyboardButton(text=BTN_ADD_TIME, callback_data="add_time")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_hour_keyboard() -> InlineKeyboardMarkup:
    """Soat tanlash: 00–23, callback sch_h_0 … sch_h_23 (4 qator x 6 tugma)."""
    rows = []
    for h in range(24):
        btn = InlineKeyboardButton(text=f"{h:02d}", callback_data=f"sch_h_{h}")
        if not rows or len(rows[-1]) >= 6:
            rows.append([btn])
        else:
            rows[-1].append(btn)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_minute_keyboard() -> InlineKeyboardMarkup:
    """Minut tanlash: 00, 15, 30, 45 — callback sch_m_00, sch_m_15, …"""
    minutes = ("00", "15", "30", "45")
    row = [InlineKeyboardButton(text=m, callback_data=f"sch_m_{m}") for m in minutes]
    return InlineKeyboardMarkup(inline_keyboard=[row])


def banner_confirm_keyboard() -> InlineKeyboardMarkup:
    """After photo received: Banner sifatida saqlash, Rasmni bot pic qilish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_SAVE_AS_BANNER, callback_data="confirm_banner")],
        [InlineKeyboardButton(text=BTN_SET_BOT_PIC, callback_data="confirm_bot_pic")],
    ])


def confirm_target_group_keyboard() -> InlineKeyboardMarkup:
    """After target group ID entered: Guruhni belgilash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CONFIRM_TARGET_GROUP, callback_data="confirm_target_group")],
    ])


def confirm_admin_group_keyboard() -> InlineKeyboardMarkup:
    """After lead group ID entered: Guruhni belgilash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CONFIRM_ADMIN_GROUP, callback_data="confirm_admin_group")],
    ])


def admin_main_inline_keyboard() -> InlineKeyboardMarkup:
    """Admin/Owner: asosiy amallar — Postlar tarixi, Nashr vaqtlari, Yoqish/O'chirish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_INLINE_HISTORY, callback_data="inline_history"),
            InlineKeyboardButton(text=BTN_INLINE_SCHEDULE, callback_data="inline_schedule"),
        ],
        [
            InlineKeyboardButton(text=BTN_INLINE_POST_ON, callback_data="cb_post_on"),
            InlineKeyboardButton(text=BTN_INLINE_POST_OFF, callback_data="cb_post_off"),
        ],
    ])


def owner_admin_list_keyboard(admins: list) -> InlineKeyboardMarkup:
    """Owner: admin ro'yxati — har bir admin uchun O'chirish tugmasi (callback remove_admin_{telegram_id})."""
    rows = []
    for a in admins:
        tid = getattr(a, "telegram_id", a) if hasattr(a, "telegram_id") else a
        rows.append([
            InlineKeyboardButton(text="O'chirish", callback_data=f"remove_admin_{tid}"),
        ])
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
