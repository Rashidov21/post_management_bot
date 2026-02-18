# -*- coding: utf-8 -*-
"""
Admin handlers: content, schedule, history, settings. Excludes owner-only commands.
"""
import logging
import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.texts import (
    HELP_HEADER,
    CMD_START, CMD_HELP, CMD_SET_TIMES, CMD_POST_ON, CMD_POST_OFF,
    CMD_HISTORY, CMD_DELETE_POST, CMD_ACTIVATE_POST, CMD_SET_BANNER, CMD_ADD_TEXT, ADD_TEXT_EMPTY,
    CMD_SET_TARGET_GROUP, CMD_SET_ADMIN_GROUP,
    POSTING_ON, POSTING_OFF, TIMES_SET, TARGET_GROUP_SET, ADMIN_GROUP_SET, BANNER_SET,
    GROUP_ID_SHOULD_BE_NEGATIVE,
    CONTENT_SAVED, NO_ACTIVE_CONTENT, HISTORY_HEADER, POST_DELETED, POST_ACTIVATED, POST_NOT_FOUND, POST_ALREADY_ACTIVE,
    SCHEDULE_ADDED, SCHEDULE_REMOVED, SCHEDULE_INVALID, CURRENT_TIMES,
    SCHEDULE_ADD_TIME_HINT,
    ADMIN_ONLY,
)
from bot.services import (
    content_service,
    schedule_service,
    settings_service,
    leads_service,
    admin_service,
)
from bot.texts import (
    BTN_HELP,
    BTN_HISTORY,
    BTN_POST_ON,
    BTN_POST_OFF,
    BTN_SCHEDULE,
    BTN_BANNER,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
)
from bot.keyboards.reply import admin_main_keyboard
from bot.keyboards.inline import (
    history_refresh_keyboard,
    history_actions_keyboard,
    schedule_keyboard,
    admin_main_inline_keyboard,
)
from config import OWNER_ID

logger = logging.getLogger(__name__)

# Reply keyboard tugma matnlari — admin_text_ignored_for_content ularni yutmasin, maxsus handlerlar ishlasin
_ADMIN_BUTTON_TEXTS = frozenset({
    BTN_HELP,
    BTN_HISTORY,
    BTN_POST_ON,
    BTN_POST_OFF,
    BTN_SCHEDULE,
    BTN_BANNER,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
})


def _admin_kb(message: Message):
    return admin_main_keyboard(include_owner=message.from_user.id == OWNER_ID)
router = Router(name="admin")


def _help_text() -> str:
    return "\n".join([
        HELP_HEADER,
        CMD_START,
        CMD_HELP,
        CMD_SET_TIMES,
        CMD_POST_ON,
        CMD_POST_OFF,
        CMD_HISTORY,
        CMD_DELETE_POST,
        CMD_ACTIVATE_POST,
        CMD_SET_BANNER,
        CMD_ADD_TEXT,
        CMD_SET_TARGET_GROUP,
        CMD_SET_ADMIN_GROUP,
    ])


@router.message(F.chat.type == "private", F.text == "/help")
@router.message(F.chat.type == "private", F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(
        _help_text(),
        reply_markup=admin_main_inline_keyboard(),
    )


# ---------- Content: photo, video, text ----------
@router.message(F.chat.type == "private", F.photo)
async def admin_save_photo(message: Message) -> None:
    photo = message.photo[-1]
    await content_service.add_content(
        content_type="photo",
        created_by=message.from_user.id,
        file_id=photo.file_id,
        caption=message.caption,
    )
    await message.answer(CONTENT_SAVED, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.video)
async def admin_save_video(message: Message) -> None:
    await content_service.add_content(
        content_type="video",
        created_by=message.from_user.id,
        file_id=message.video.file_id,
        caption=message.caption,
    )
    await message.answer(CONTENT_SAVED, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/add_text\s+(.+)$", re.DOTALL)))
async def admin_add_text_content(message: Message) -> None:
    """Add text-only post: /add_text <matn>."""
    match = re.match(r"^/add_text\s+(.+)$", message.text, re.DOTALL)
    if not match:
        return
    text = match.group(1).strip()
    if not text:
        await message.answer(ADD_TEXT_EMPTY, reply_markup=_admin_kb(message))
        return
    await content_service.add_content(
        content_type="text",
        created_by=message.from_user.id,
        text=text,
    )
    await message.answer(CONTENT_SAVED, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/add_text\s*$")))
async def admin_add_text_empty(message: Message) -> None:
    """Prompt when /add_text has no body."""
    await message.answer(ADD_TEXT_EMPTY, reply_markup=_admin_kb(message))


@router.message(
    F.chat.type == "private",
    F.text,
    F.text.startswith("/") == False,
    F.text.filter(lambda t: t not in _ADMIN_BUTTON_TEXTS),
)
async def admin_text_ignored_for_content(message: Message) -> None:
    """Non-command, non-button text from admin in private: consumed here (user router does not run for admins)."""
    pass


# ---------- Schedule ----------
@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/set_times\s+(.+)$", re.I)))
async def cmd_set_times(message: Message) -> None:
    """e.g. /set_times 09:00, 14:00, 18:00 - replace or add times."""
    match = message.text and re.match(r"^/set_times\s+(.+)$", message.text, re.I)
    if not match:
        return
    raw = match.group(1).strip()
    parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
    added = []
    for p in parts:
        t = schedule_service.parse_time(p)
        if t:
            await schedule_service.add_schedule(t)
            added.append(t)
    if added:
        times_str = ", ".join(await _format_times())
        await message.answer(
            TIMES_SET + "\n" + CURRENT_TIMES.format(times_str),
            reply_markup=_admin_kb(message),
        )
    else:
        await message.answer(SCHEDULE_INVALID, reply_markup=_admin_kb(message))


async def _format_times() -> list:
    schedules = await schedule_service.list_schedules()
    return [s.time_str for s in schedules]


@router.message(F.chat.type == "private", F.text == "/post_on")
@router.message(F.chat.type == "private", F.text == BTN_POST_ON)
async def cmd_post_on(message: Message) -> None:
    await settings_service.set_posting_enabled(True)
    await message.answer(POSTING_ON, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.text == "/post_off")
@router.message(F.chat.type == "private", F.text == BTN_POST_OFF)
async def cmd_post_off(message: Message) -> None:
    await settings_service.set_posting_enabled(False)
    await message.answer(POSTING_OFF, reply_markup=_admin_kb(message))


# ---------- History & delete ----------
def _format_posted_at(dt) -> str:
    """Format datetime for 'oxirgi nashr' display."""
    if dt is None:
        return "—"
    if hasattr(dt, "strftime"):
        return dt.strftime("%d.%m.%Y %H:%M")
    return str(dt)


async def _send_history(target):
    """Send or edit history list with last posted time and refresh inline button."""
    posts = await content_service.list_all_posts_for_history(limit=20)
    if not posts:
        text = HISTORY_HEADER + "\n(bo'sh)"
    else:
        cids = [p.id for p in posts]
        last_posted = await content_service.get_last_posted_at_map(cids)
        lines = [HISTORY_HEADER]
        for p in posts:
            status = "✅" if p.status == "active" else "❌"
            posted_str = _format_posted_at(last_posted.get(p.id))
            lines.append(f"{status} ID: {p.id} | {p.content_type} | yaratilgan: {p.created_at} | oxirgi nashr: {posted_str}")
        text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4090] + "\n…"
    kb = history_actions_keyboard(posts)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


@router.message(F.chat.type == "private", F.text == "/history")
@router.message(F.chat.type == "private", F.text == BTN_HISTORY)
async def cmd_history(message: Message) -> None:
    await _send_history(message)


@router.callback_query(F.data == "refresh_history")
async def cb_refresh_history(callback: CallbackQuery) -> None:
    await _send_history(callback)
    await callback.answer("Yangilandi.")


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/delete_post\s+(\d+)$")))
async def cmd_delete_post(message: Message) -> None:
    match = message.text and re.match(r"^/delete_post\s+(\d+)$", message.text)
    if not match:
        return
    cid = int(match.group(1))
    ok = await content_service.delete_content(cid)
    if ok:
        await message.answer(POST_DELETED, reply_markup=_admin_kb(message))
    else:
        await message.answer(POST_NOT_FOUND, reply_markup=_admin_kb(message))


@router.callback_query(F.data.regexp(re.compile(r"^del_post_(\d+)$")))
async def cb_delete_post(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^del_post_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    cid = int(match.group(1))
    ok = await content_service.delete_content(cid)
    if ok:
        await callback.answer(POST_DELETED)
        await callback.message.edit_text((callback.message.text or "") + "\n\n" + POST_DELETED)
    else:
        await callback.answer(POST_NOT_FOUND)


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/activate_post\s+(\d+)$")))
async def cmd_activate_post(message: Message) -> None:
    """Set a deleted post as active again."""
    match = message.text and re.match(r"^/activate_post\s+(\d+)$", message.text)
    if not match:
        return
    cid = int(match.group(1))
    content = await content_service.get_content_by_id(cid)
    if not content:
        await message.answer(POST_NOT_FOUND, reply_markup=_admin_kb(message))
        return
    if content.status == "active":
        await message.answer(POST_ALREADY_ACTIVE, reply_markup=_admin_kb(message))
        return
    ok = await content_service.set_content_active(cid)
    if ok:
        await message.answer(POST_ACTIVATED, reply_markup=_admin_kb(message))
    else:
        await message.answer(POST_NOT_FOUND, reply_markup=_admin_kb(message))


@router.callback_query(F.data.regexp(re.compile(r"^activate_post_(\d+)$")))
async def cb_activate_post(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^activate_post_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    cid = int(match.group(1))
    content = await content_service.get_content_by_id(cid)
    if not content:
        await callback.answer(POST_NOT_FOUND)
        return
    if content.status == "active":
        await callback.answer(POST_ALREADY_ACTIVE)
        return
    ok = await content_service.set_content_active(cid)
    if ok:
        await callback.answer(POST_ACTIVATED)
        await _send_history(callback)
    else:
        await callback.answer(POST_NOT_FOUND)


# ---------- Banner ----------
@router.message(F.chat.type == "private", F.photo, F.caption.regexp(re.compile(r"^/set_banner", re.I)))
async def admin_set_banner(message: Message) -> None:
    photo = message.photo[-1]
    await settings_service.set_banner_file_id(photo.file_id)
    await message.answer(BANNER_SET, reply_markup=_admin_kb(message))


# ---------- Target group: admin sends /set_target_group in the group ----------
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text == "/set_target_group")
async def cmd_set_target_group_in_group(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    if uid != OWNER_ID and not await admin_service.is_admin(uid):
        await message.answer(ADMIN_ONLY)
        return
    gid = message.chat.id
    await settings_service.set_target_group_id(gid)
    await message.answer(TARGET_GROUP_SET)


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/set_target_group\s+(-?\d+)$")))
async def cmd_set_target_group_id_private(message: Message) -> None:
    """Set target group by ID from private chat: /set_target_group -1001234567890."""
    match = message.text and re.match(r"^/set_target_group\s+(-?\d+)$", message.text)
    if not match:
        return
    gid = int(match.group(1))
    if gid >= 0:
        await message.answer(GROUP_ID_SHOULD_BE_NEGATIVE, reply_markup=_admin_kb(message))
        return
    await settings_service.set_target_group_id(gid)
    await message.answer(TARGET_GROUP_SET, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.text == "/set_target_group")
@router.message(F.chat.type == "private", F.text == BTN_TARGET_GROUP)
async def cmd_set_target_group_private(message: Message) -> None:
    await message.answer(
        "Nashr guruhida /set_target_group buyrug'ini yuboring yoki guruh ID bilan: /set_target_group -1001234567890",
        reply_markup=_admin_kb(message),
    )


@router.message(F.chat.type == "private", F.text == BTN_SCHEDULE)
async def btn_schedule(message: Message) -> None:
    schedules = await schedule_service.list_schedules()
    times_str = ", ".join(s.time_str for s in schedules) if schedules else "—"
    text = CURRENT_TIMES.format(times_str) + "\n\n" + SCHEDULE_ADD_TIME_HINT
    await message.answer(text, reply_markup=schedule_keyboard(schedules))


async def _send_schedule_message(target, reply_markup=None):
    """Send or edit schedule list (for message or callback)."""
    schedules = await schedule_service.list_schedules()
    times_str = ", ".join(s.time_str for s in schedules) if schedules else "—"
    text = CURRENT_TIMES.format(times_str) + "\n\n" + SCHEDULE_ADD_TIME_HINT
    kb = schedule_keyboard(schedules) if reply_markup is None else reply_markup
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(re.compile(r"^del_time_(.+)$")))
async def cb_del_time(callback: CallbackQuery) -> None:
    """Vaqtni o'chirish: del_time_09_00 -> 09:00."""
    match = callback.data and re.match(r"^del_time_(.+)$", callback.data)
    if not match:
        await callback.answer()
        return
    time_encoded = match.group(1)
    time_str = time_encoded.replace("_", ":", 1)
    ok = await schedule_service.remove_schedule(time_str)
    if ok:
        await callback.answer(SCHEDULE_REMOVED.format(time_str))
        schedules = await schedule_service.list_schedules()
        times_str = ", ".join(s.time_str for s in schedules) if schedules else "—"
        text = CURRENT_TIMES.format(times_str) + "\n\n" + SCHEDULE_ADD_TIME_HINT
        await callback.message.edit_text(text, reply_markup=schedule_keyboard(schedules))
    else:
        await callback.answer(SCHEDULE_INVALID)


@router.callback_query(F.data == "add_time")
async def cb_add_time(callback: CallbackQuery) -> None:
    await callback.answer(SCHEDULE_ADD_TIME_HINT, show_alert=True)


@router.callback_query(F.data == "cb_post_on")
async def cb_post_on(callback: CallbackQuery) -> None:
    await settings_service.set_posting_enabled(True)
    await callback.answer(POSTING_ON)


@router.callback_query(F.data == "cb_post_off")
async def cb_post_off(callback: CallbackQuery) -> None:
    await settings_service.set_posting_enabled(False)
    await callback.answer(POSTING_OFF)


@router.callback_query(F.data == "inline_history")
async def cb_inline_history(callback: CallbackQuery) -> None:
    await _send_history(callback)
    await callback.answer()


@router.callback_query(F.data == "inline_schedule")
async def cb_inline_schedule(callback: CallbackQuery) -> None:
    await _send_schedule_message(callback)
    await callback.answer()


@router.message(F.chat.type == "private", F.text == BTN_BANNER)
async def btn_banner(message: Message) -> None:
    await message.answer(
        "Banner o'rnatish: rasm yuboring, captionda /set_banner yozing.",
        reply_markup=_admin_kb(message),
    )


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text == "/set_admin_group")
async def cmd_set_admin_group_in_group(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    if uid != OWNER_ID and not await admin_service.is_admin(uid):
        await message.answer(ADMIN_ONLY)
        return
    gid = message.chat.id
    await settings_service.set_admin_group_id(gid)
    await message.answer(ADMIN_GROUP_SET)


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/set_admin_group\s+(-?\d+)$")))
async def cmd_set_admin_group_id_private(message: Message) -> None:
    """Set admin group by ID from private chat: /set_admin_group -1001234567890."""
    match = message.text and re.match(r"^/set_admin_group\s+(-?\d+)$", message.text)
    if not match:
        return
    gid = int(match.group(1))
    if gid >= 0:
        await message.answer(GROUP_ID_SHOULD_BE_NEGATIVE, reply_markup=_admin_kb(message))
        return
    await settings_service.set_admin_group_id(gid)
    await message.answer(ADMIN_GROUP_SET, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.text == "/set_admin_group")
@router.message(F.chat.type == "private", F.text == BTN_LEAD_GROUP)
async def cmd_set_admin_group_private(message: Message) -> None:
    await message.answer(
        "Leadlar yuboriladigan guruhda /set_admin_group buyrug'ini yuboring yoki guruh ID: /set_admin_group -1001234567890",
        reply_markup=_admin_kb(message),
    )


# ---------- Take lead callback (admin group) ----------
@router.callback_query(F.data.regexp(re.compile(r"^take_lead_(\d+)$")))
async def cb_take_lead(callback: CallbackQuery) -> None:
    from config import OWNER_ID
    from bot.services import admin_service
    from bot.texts import LEAD_TAKEN, LEAD_ALREADY_TAKEN

    match = callback.data and re.match(r"^take_lead_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    lead_id = int(match.group(1))
    admin_telegram_id = callback.from_user.id if callback.from_user else 0
    is_admin_user = admin_telegram_id == OWNER_ID or await admin_service.is_admin(admin_telegram_id)
    if not is_admin_user:
        await callback.answer("Faqat adminlar leadni olishi mumkin.")
        return
    ok = await leads_service.take_lead(lead_id, admin_telegram_id)
    if ok:
        await callback.answer(LEAD_TAKEN)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"✅ Lead #{lead_id} — admin tomonidan olindi.")
        except Exception:
            pass
    else:
        await callback.answer(LEAD_ALREADY_TAKEN)


# ---------- Owner inline: admin list / help (only owner can use) ----------
@router.callback_query(F.data == "admin_list")
async def cb_admin_list(callback: CallbackQuery) -> None:
    from config import OWNER_ID
    from bot.services import admin_service
    from bot.texts import LIST_ADMINS_HEADER

    if callback.from_user.id != OWNER_ID:
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    admins = await admin_service.list_admins()
    if not admins:
        text = LIST_ADMINS_HEADER + "\n(bo'sh)"
    else:
        lines = [LIST_ADMINS_HEADER]
        for a in admins:
            uname = f"@{a.username}" if a.username else ""
            lines.append(f"- {a.telegram_id} {uname}")
        text = "\n".join(lines)
    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "admin_help_add")
async def cb_admin_help_add(callback: CallbackQuery) -> None:
    from config import OWNER_ID
    from bot.texts import REPLY_TO_ADD_ADMIN

    if callback.from_user.id != OWNER_ID:
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    await callback.message.edit_text(REPLY_TO_ADD_ADMIN)
    await callback.answer()


@router.callback_query(F.data == "admin_help_remove")
async def cb_admin_help_remove(callback: CallbackQuery) -> None:
    from config import OWNER_ID
    from bot.texts import REPLY_TO_REMOVE_ADMIN

    if callback.from_user.id != OWNER_ID:
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    await callback.message.edit_text(REPLY_TO_REMOVE_ADMIN)
    await callback.answer()
