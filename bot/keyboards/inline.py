# -*- coding: utf-8 -*-
"""
Inline keyboards for user and admin flows.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts import (
    CONTACT_ADMIN_BUTTON,
    BTN_CONTACT_ADMINS_UNDER_POST,
    TAKE_LEAD,  # "Leadni olish" — lead actions keyboard da
    BTN_ADMIN_LIST,
    BTN_ADMIN_ADD_HINT,
    BTN_ADMIN_REMOVE_HINT,
    BTN_REFRESH_HISTORY,
    BTN_ADD_TIME,
    BTN_POST_NOW,
    BTN_HISTORY_BACK,
    BTN_INLINE_HISTORY,
    BTN_INLINE_SCHEDULE,
    BTN_CONFIRM_TARGET_GROUP,
    BTN_CONFIRM_ADMIN_GROUP,
    BTN_POST_CONFIRM,
    BTN_POST_CANCEL,
    POST_NOT_ASSIGNED,
    BTN_ASSIGN_POST,
    BTN_PUBLISHING_ON,
    BTN_PUBLISHING_OFF,
    BTN_NAV_HOME,
)


def contact_bot_for_post_keyboard(bot_username: str, content_id: int) -> InlineKeyboardMarkup:
    """
    Guruhdagi post ostida: bitta tugma — botga ?start=post_<id> orqali.
    User shu post kontekstida xabar yozadi, adminlar guruhida qaysi post ekani ko'rinadi.
    """
    url = f"https://t.me/{bot_username}?start=post_{content_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CONTACT_ADMINS_UNDER_POST, url=url)],
    ])


async def contact_admin_keyboard() -> InlineKeyboardMarkup:
    """
    Build contact buttons for all admins:
    - If username: https://t.me/<username>
    - Else: tg://user?id=<telegram_id>
    Fallback: bot start link if admin list is empty.
    """
    from bot.services import admin_service
    admins = await admin_service.list_admins()
    rows = []
    for a in admins:
        uname = getattr(a, "username", None)
        if uname:
            url = f"https://t.me/{uname}"
        else:
            url = f"tg://user?id={getattr(a, 'telegram_id', 0)}"
        label = f"{CONTACT_ADMIN_BUTTON} – {uname or getattr(a, 'telegram_id', '')}"
        rows.append([InlineKeyboardButton(text=label, url=url)])
    if not rows:
        rows.append([InlineKeyboardButton(text=CONTACT_ADMIN_BUTTON, url="https://t.me/")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def lead_actions_keyboard(lead_id: int, user_id: int, username: str | None) -> InlineKeyboardMarkup:
    """Inline actions for lead in admin group: Leadni olish, Chatga o'tish."""
    url = f"https://t.me/{username}" if username else f"tg://user?id={user_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TAKE_LEAD, callback_data=f"take_lead_{lead_id}")],
        [InlineKeyboardButton(text="💬 Chatga o'tish", url=url)],
    ])


def leads_list_keyboard(leads: list) -> InlineKeyboardMarkup:
    """List of unanswered leads: Leadni olish, Chat."""
    rows = []
    for lead in leads:
        url = f"tg://user?id={lead.telegram_user_id}"
        rows.append([
            InlineKeyboardButton(text=TAKE_LEAD, callback_data=f"take_lead_{lead.id}"),
            InlineKeyboardButton(text="💬 Chat", url=url),
        ])
    if not rows:
        rows.append([InlineKeyboardButton(text="—", callback_data="noop")])
    rows.append([InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
    """Nashr vaqtlari: har bir vaqt uchun Post tanlash + O'chirish, oxirida Vaqt qo'shish."""
    return schedule_keyboard_with_posts(schedules, {})


def schedule_keyboard_with_posts(
    schedules: list,
    schedule_content_map: dict,
) -> InlineKeyboardMarkup:
    """schedule_content_map: schedule_id -> (content_id, caption_preview) or None."""
    rows = []
    for s in schedules:
        sid = getattr(s, "id", None)
        time_str = getattr(s, "time_str", str(s))
        time_enc = time_str.replace(":", "_")
        rows.append([
            InlineKeyboardButton(text=BTN_ASSIGN_POST, callback_data=f"assign_post_{sid}" if sid is not None else f"assign_post_0"),
            InlineKeyboardButton(text="O'chirish", callback_data=f"del_time_{time_enc}"),
        ])
    rows.append([InlineKeyboardButton(text=BTN_ADD_TIME, callback_data="add_time")])
    rows.append([InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def schedule_pick_post_keyboard(schedule_id: int, posts: list) -> InlineKeyboardMarkup:
    """Post tanlash: har bir post uchun tugma (assign_schedule_{schedule_id}_content_{content_id}), oxirida Orqaga."""
    rows = []
    for p in posts:
        cap = (getattr(p, "caption", None) or getattr(p, "text", None) or "").strip() or f"#{getattr(p, 'id', p)}"
        if len(cap) > 35:
            cap = cap[:32] + "…"
        label = f"#{getattr(p, 'id', p)}: {cap}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"assign_schedule_{schedule_id}_content_{getattr(p, 'id', p)}")])
    rows.append([
        InlineKeyboardButton(text=BTN_HISTORY_BACK, callback_data="schedule_back"),
        InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home"),
    ])
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
    """Minut tanlash: 00–59 — callback sch_m_00 … sch_m_59 (6 tugma qatorda)."""
    minutes = [f"{m:02d}" for m in range(60)]
    rows = []
    for i in range(0, 60, 6):
        row = [InlineKeyboardButton(text=m, callback_data=f"sch_m_{m}") for m in minutes[i : i + 6]]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_target_group_keyboard() -> InlineKeyboardMarkup:
    """After target group ID entered: Guruhni belgilash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CONFIRM_TARGET_GROUP, callback_data="confirm_target_group")],
    ])


def confirm_admin_group_keyboard() -> InlineKeyboardMarkup:
    """After lead group ID entered: Guruhni belgilash."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=BTN_CONFIRM_ADMIN_GROUP, callback_data="confirm_admin_group")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_admin_group")],
        [InlineKeyboardButton(text=BTN_NAV_HOME, callback_data="nav_home")],
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
    """Admin/Owner: asosiy amallar — Postlar tarixi, Nashr vaqtlari, Leadlar."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_INLINE_HISTORY, callback_data="inline_history"),
            InlineKeyboardButton(text=BTN_INLINE_SCHEDULE, callback_data="inline_schedule"),
        ],
        [
            InlineKeyboardButton(text="🧾 Leadlar", callback_data="inline_leads"),
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
