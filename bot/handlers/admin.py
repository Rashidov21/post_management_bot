# -*- coding: utf-8 -*-
"""
Admin handlers: content, schedule, history, settings. Excludes owner-only commands.
"""
import logging
import re

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter

from bot.texts import (
    HELP_HEADER,
    CMD_START, CMD_HELP, CMD_SET_TIMES, CMD_POST_ON, CMD_POST_OFF,
    CMD_HISTORY, CMD_DELETE_POST, CMD_ACTIVATE_POST, CMD_SET_BANNER, CMD_ADD_TEXT, ADD_TEXT_EMPTY,
    CMD_SET_TARGET_GROUP, CMD_SET_ADMIN_GROUP,
    POSTING_ON, POSTING_OFF, TIMES_SET, TARGET_GROUP_SET, TARGET_GROUP_PROMPT_ID, TARGET_GROUP_ID_RECEIVED,
    ADMIN_GROUP_SET, ADMIN_GROUP_PROMPT_ID, ADMIN_GROUP_ID_RECEIVED,
    BANNER_SET,
    GROUP_ID_SHOULD_BE_NEGATIVE,
    CONTENT_SAVED, NO_ACTIVE_CONTENT, HISTORY_HEADER, HISTORY_SINGLE_HEADER, POST_DELETED, POST_ACTIVATED, POST_NOT_FOUND, POST_ALREADY_ACTIVE,
    SCHEDULE_ADDED, SCHEDULE_REMOVED, SCHEDULE_INVALID, CURRENT_TIMES,
    SCHEDULE_ADD_TIME_HINT,
    SCHEDULE_PICK_HOUR, SCHEDULE_PICK_MINUTE, SCHEDULE_TIME_ADDED,
    POST_NOW_SUCCESS, POST_NOW_FAILED,
    BANNER_SEND_PHOTO, BANNER_PHOTO_RECEIVED, BOT_PIC_ONLY_BOTFATHER,
    ADMIN_REMOVED, ADMIN_NOT_FOUND,
    ADMIN_ADD_PROMPT, ADMIN_ADD_INVALID_ID,
    ADMIN_ONLY,
)
from bot.services import (
    content_service,
    schedule_service,
    settings_service,
    leads_service,
    admin_service,
)
from bot.scheduler import posting as posting_module
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
    history_list_keyboard,
    history_single_keyboard,
    schedule_keyboard,
    schedule_hour_keyboard,
    schedule_minute_keyboard,
    banner_confirm_keyboard,
    confirm_target_group_keyboard,
    confirm_admin_group_keyboard,
    owner_admin_list_keyboard,
    admin_main_inline_keyboard,
)
from config import is_owner

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
    return admin_main_keyboard(include_owner=is_owner(message.from_user.id or 0))
router = Router(name="admin")

# Vaqt qo'shish: soat tanlang -> minut tanlang -> add_schedule
_schedule_pending: dict[int, dict] = {}
# Banner: rasm kutiladi, keyin inline Banner / Bot pic
_banner_waiting_photo: set[int] = set()
_banner_pending_file: dict[int, str] = {}
# Nashr guruhi: ID kiritiladi, keyin inline tasdiq
_target_group_awaiting: set[int] = set()
_target_group_pending: dict[int, int] = {}
# Lead guruhi: ID kiritiladi, keyin inline tasdiq
_admin_group_awaiting: set[int] = set()
_admin_group_pending: dict[int, int] = {}
# Admin qo'shish: owner ID kiritadi (Adminlar → Qo'shish)
_admin_add_awaiting: set[int] = set()


class _AdminAddAwaitingFilter(Filter):
    """True when user is in admin-add flow (entering ID)."""

    async def __call__(self, message: Message) -> bool:
        return (message.from_user.id if message.from_user else 0) in _admin_add_awaiting


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
    uid = message.from_user.id if message.from_user else 0
    if uid in _banner_waiting_photo:
        _banner_waiting_photo.discard(uid)
        photo = message.photo[-1]
        _banner_pending_file[uid] = photo.file_id
        await message.answer(BANNER_PHOTO_RECEIVED, reply_markup=banner_confirm_keyboard())
        return
    photo = message.photo[-1]
    await content_service.add_content(
        content_type="photo",
        created_by=uid,
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
    """Send or edit history list (last 10), each post selectable; refresh button."""
    posts = await content_service.list_all_posts_for_history(limit=10)
    if not posts:
        text = HISTORY_HEADER + "\n(bo'sh)"
        kb = history_list_keyboard([])
    else:
        cids = [p.id for p in posts]
        last_posted = await content_service.get_last_posted_at_map(cids)
        lines = [HISTORY_HEADER]
        for p in posts:
            status = "✅" if p.status == "active" else "❌"
            posted_str = _format_posted_at(last_posted.get(p.id))
            lines.append(f"{status} ID: {p.id} | {p.content_type} | yaratilgan: {p.created_at} | oxirgi nashr: {posted_str}")
        text = "\n".join(lines)
        kb = history_list_keyboard(posts)
    if len(text) > 4096:
        text = text[:4090] + "\n…"
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


@router.callback_query(F.data == "history_back")
async def cb_history_back(callback: CallbackQuery) -> None:
    await _send_history(callback)
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^history_show_(\d+)$")))
async def cb_history_show(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^history_show_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    cid = int(match.group(1))
    post = await content_service.get_content_by_id(cid)
    if not post:
        await callback.answer(POST_NOT_FOUND)
        return
    last_posted = await content_service.get_last_posted_at_map([cid])
    posted_str = _format_posted_at(last_posted.get(cid))
    created_str = str(post.created_at) if post.created_at else "—"
    text = HISTORY_SINGLE_HEADER.format(
        id=post.id,
        content_type=post.content_type,
        created_at=created_str,
        posted=posted_str,
    )
    await callback.message.edit_text(text, reply_markup=history_single_keyboard(post))
    await callback.answer()


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
        await _send_history(callback)
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


@router.callback_query(F.data.regexp(re.compile(r"^post_now_(\d+)$")))
async def cb_post_now(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^post_now_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    content_id = int(match.group(1))
    me = await callback.bot.get_me()
    bot_username = me.username or ""
    ok = await posting_module.post_content_by_id_to_group(callback.bot, bot_username, content_id)
    if ok:
        await callback.answer(POST_NOW_SUCCESS)
        await _send_history(callback)
    else:
        await callback.answer(POST_NOW_FAILED)


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
    if not is_owner(uid) and not await admin_service.is_admin(uid):
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
    uid = message.from_user.id if message.from_user else 0
    _target_group_awaiting.add(uid)
    await message.answer(TARGET_GROUP_PROMPT_ID, reply_markup=_admin_kb(message))


@router.message(F.chat.type == "private", F.text, _AdminAddAwaitingFilter())
async def admin_add_by_id_message(message: Message) -> None:
    """Owner: Admin qo'shish — ID kiritilganda (Adminlar → Qo'shish → raqam)."""
    uid = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()
    _admin_add_awaiting.discard(uid)
    if not text.isdigit():
        await message.answer(ADMIN_ADD_INVALID_ID, reply_markup=_admin_kb(message))
        return
    telegram_id = int(text)
    if await admin_service.is_admin(telegram_id):
        await message.answer(ADMIN_ALREADY, reply_markup=_admin_kb(message))
        return
    ok = await admin_service.add_admin(telegram_id, None)
    await message.answer(
        ADMIN_ADDED if ok else "Xatolik yuz berdi.",
        reply_markup=_admin_kb(message),
    )


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^-?\d+$")))
async def admin_text_group_id(message: Message) -> None:
    """Accept target or lead group ID when user is in corresponding awaiting set."""
    uid = message.from_user.id if message.from_user else 0
    gid = int(message.text.strip())
    if uid in _target_group_awaiting:
        _target_group_awaiting.discard(uid)
        _target_group_pending[uid] = gid
        await message.answer(TARGET_GROUP_ID_RECEIVED, reply_markup=confirm_target_group_keyboard())
    elif uid in _admin_group_awaiting:
        _admin_group_awaiting.discard(uid)
        _admin_group_pending[uid] = gid
        await message.answer(ADMIN_GROUP_ID_RECEIVED, reply_markup=confirm_admin_group_keyboard())


@router.callback_query(F.data == "confirm_target_group")
async def cb_confirm_target_group(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    gid = _target_group_pending.pop(uid, None)
    if gid is not None:
        await settings_service.set_target_group_id(gid)
        await callback.answer(TARGET_GROUP_SET)
    else:
        await callback.answer()


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
    await callback.message.edit_text(SCHEDULE_PICK_HOUR, reply_markup=schedule_hour_keyboard())
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^sch_h_(\d+)$")))
async def cb_schedule_hour(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^sch_h_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    hour = int(match.group(1))
    uid = callback.from_user.id if callback.from_user else 0
    _schedule_pending[uid] = {"hour": hour}
    await callback.message.edit_text(SCHEDULE_PICK_MINUTE, reply_markup=schedule_minute_keyboard())
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^sch_m_(\d{2})$")))
async def cb_schedule_minute(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^sch_m_(\d{2})$", callback.data)
    if not match:
        await callback.answer()
        return
    minute_str = match.group(1)
    uid = callback.from_user.id if callback.from_user else 0
    pending = _schedule_pending.pop(uid, None)
    if not pending or "hour" not in pending:
        await callback.answer(SCHEDULE_INVALID)
        return
    hour = pending["hour"]
    time_str = f"{hour:02d}:{minute_str}"
    ok = await schedule_service.add_schedule(time_str)
    if ok:
        await callback.answer(SCHEDULE_TIME_ADDED)
        await _send_schedule_message(callback)
    else:
        await callback.answer(SCHEDULE_INVALID)


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


@router.callback_query(F.data == "confirm_banner")
async def cb_confirm_banner(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    file_id = _banner_pending_file.pop(uid, None)
    if file_id:
        await settings_service.set_banner_file_id(file_id)
        await callback.answer(BANNER_SET)
    else:
        await callback.answer()


@router.callback_query(F.data == "confirm_bot_pic")
async def cb_confirm_bot_pic(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    file_id = _banner_pending_file.pop(uid, None)
    if not file_id:
        await callback.answer()
        return
    try:
        # aiogram 3.25+ has set_my_profile_photo; 3.22 may not
        method = getattr(callback.bot, "set_my_profile_photo", None)
        if method:
            result = await method(photo=file_id)
            if result:
                await callback.answer("Bot rasmi yangilandi.")
            else:
                await callback.answer(BOT_PIC_ONLY_BOTFATHER)
        else:
            await callback.answer(BOT_PIC_ONLY_BOTFATHER)
    except Exception:
        await callback.answer(BOT_PIC_ONLY_BOTFATHER)


@router.message(F.chat.type == "private", F.text == BTN_BANNER)
async def btn_banner(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _banner_waiting_photo.add(uid)
    await message.answer(BANNER_SEND_PHOTO, reply_markup=_admin_kb(message))


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text == "/set_admin_group")
async def cmd_set_admin_group_in_group(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    if not is_owner(uid) and not await admin_service.is_admin(uid):
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
    uid = message.from_user.id if message.from_user else 0
    _admin_group_awaiting.add(uid)
    await message.answer(ADMIN_GROUP_PROMPT_ID, reply_markup=_admin_kb(message))


@router.callback_query(F.data == "confirm_admin_group")
async def cb_confirm_admin_group(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    gid = _admin_group_pending.pop(uid, None)
    if gid is not None:
        await settings_service.set_admin_group_id(gid)
        await callback.answer(ADMIN_GROUP_SET)
    else:
        await callback.answer()


# ---------- Take lead callback (admin group) ----------
@router.callback_query(F.data.regexp(re.compile(r"^take_lead_(\d+)$")))
async def cb_take_lead(callback: CallbackQuery) -> None:
    from bot.services import admin_service
    from bot.texts import LEAD_TAKEN, LEAD_ALREADY_TAKEN

    match = callback.data and re.match(r"^take_lead_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    lead_id = int(match.group(1))
    admin_telegram_id = callback.from_user.id if callback.from_user else 0
    is_admin_user = is_owner(admin_telegram_id) or await admin_service.is_admin(admin_telegram_id)
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
def _format_admin_list_message(admins: list) -> tuple[str, object]:
    """Return (text, reply_markup) for admin list."""
    from bot.texts import LIST_ADMINS_HEADER
    if not admins:
        return LIST_ADMINS_HEADER + "\n(bo'sh)", owner_admin_list_keyboard([])
    lines = [LIST_ADMINS_HEADER]
    for a in admins:
        uname = f"@{a.username}" if getattr(a, "username", None) else ""
        lines.append(f"- {a.telegram_id} {uname}")
    text = "\n".join(lines)
    return text, owner_admin_list_keyboard(admins)


@router.callback_query(F.data == "admin_list")
async def cb_admin_list(callback: CallbackQuery) -> None:
    if not is_owner(callback.from_user.id or 0):
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    admins = await admin_service.list_admins()
    text, kb = _format_admin_list_message(admins)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^remove_admin_(\d+)$")))
async def cb_remove_admin(callback: CallbackQuery) -> None:
    if not is_owner(callback.from_user.id or 0):
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    match = callback.data and re.match(r"^remove_admin_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    telegram_id = int(match.group(1))
    ok = await admin_service.remove_admin(telegram_id)
    if ok:
        admins = await admin_service.list_admins()
        text, kb = _format_admin_list_message(admins)
        await callback.message.edit_text(text, reply_markup=kb)
        await callback.answer(ADMIN_REMOVED)
    else:
        await callback.answer(ADMIN_NOT_FOUND)


@router.callback_query(F.data == "admin_help_add")
async def cb_admin_help_add(callback: CallbackQuery) -> None:
    from bot.texts import ADMIN_ADD_PROMPT

    if not is_owner(callback.from_user.id or 0):
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    _admin_add_awaiting.add(callback.from_user.id)
    await callback.message.edit_text(ADMIN_ADD_PROMPT)
    await callback.answer()


@router.callback_query(F.data == "admin_help_remove")
async def cb_admin_help_remove(callback: CallbackQuery) -> None:
    from bot.texts import REPLY_TO_REMOVE_ADMIN

    if not is_owner(callback.from_user.id or 0):
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    await callback.message.edit_text(REPLY_TO_REMOVE_ADMIN)
    await callback.answer()
