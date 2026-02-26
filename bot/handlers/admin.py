# -*- coding: utf-8 -*-
"""
Admin handlers: content, schedule, history, settings. Excludes owner-only commands.
"""
import logging
import re

from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter

from bot.texts import (
    HELP_HEADER, HELP_GUIDE,
    ADD_TEXT_EMPTY,
    TIMES_SET, TARGET_GROUP_SET, TARGET_GROUP_PROMPT_ID, TARGET_GROUP_ID_RECEIVED,
    ADMIN_GROUP_SET, ADMIN_GROUP_PROMPT_ID, ADMIN_GROUP_ID_RECEIVED,
    GROUP_ID_SHOULD_BE_NEGATIVE,
    CONTENT_SAVED, NO_ACTIVE_CONTENT, HISTORY_HEADER, POST_DELETED, POST_NOT_FOUND,
    SCHEDULE_ADDED, SCHEDULE_REMOVED, SCHEDULE_INVALID, CURRENT_TIMES,
    SCHEDULE_ADD_TIME_HINT,
    SCHEDULE_PICK_HOUR, SCHEDULE_PICK_MINUTE, SCHEDULE_TIME_ADDED,
    POST_NOT_ASSIGNED, SCHEDULE_PICK_POST_HEADER, SCHEDULE_ASSIGNED, NASHR_TIMES_LABEL,
    POST_NOW_SUCCESS, POST_NOW_FAILED,
    ADMIN_REMOVED, ADMIN_NOT_FOUND,
    ADMIN_ADD_PROMPT, ADMIN_ADD_INVALID_ID,
    POST_ADD_SEND_MEDIA, POST_ADD_SEND_CAPTION, POST_ADD_CAPTION_ADDED,
    POST_ADD_SAVED, POST_ADD_CANCELLED,
    POST_ADD_PICK_TIME_HOUR, POST_ADD_PICK_TIME_MINUTE,
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
    BTN_ADD_POST,
    BTN_SCHEDULE,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
    BTN_ADMINS,
)
from bot.keyboards.reply import admin_main_keyboard
from bot.keyboards.inline import (
    history_refresh_keyboard,
    history_delete_keyboard,
    schedule_keyboard,
    schedule_keyboard_with_posts,
    schedule_pick_post_keyboard,
    schedule_hour_keyboard,
    schedule_minute_keyboard,
    confirm_target_group_keyboard,
    confirm_admin_group_keyboard,
    post_add_confirm_keyboard,
    post_add_schedule_hour_keyboard,
    post_add_schedule_minute_keyboard,
    owner_admin_list_keyboard,
    admin_main_inline_keyboard,
    leads_list_keyboard,
)
from config import is_owner

logger = logging.getLogger(__name__)

# Reply keyboard tugma matnlari — admin_text_ignored_for_content ularni yutmasin, maxsus handlerlar ishlasin
_ADMIN_BUTTON_TEXTS = frozenset({
    BTN_HELP,
    BTN_HISTORY,
    BTN_ADD_POST,
    BTN_SCHEDULE,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
})
# Lead reply handler bu tugmalarni yutmasin — Adminlar / Lead guruhi va b. o'z handlerlariga tushishi kerak
_REPLY_IGNORE_TEXTS = _ADMIN_BUTTON_TEXTS | frozenset({BTN_ADMINS})


def _admin_kb(message: Message):
    return admin_main_keyboard(include_owner=is_owner(message.from_user.id or 0))
router = Router(name="admin")

# Vaqt qo'shish: soat tanlang -> minut tanlang -> add_schedule
_schedule_pending: dict[int, dict] = {}
# Nashr guruhi: ID kiritiladi, keyin inline tasdiq
_target_group_awaiting: set[int] = set()
_target_group_pending: dict[int, int] = {}
# Lead guruhi: ID kiritiladi, keyin inline tasdiq
_admin_group_awaiting: set[int] = set()
_admin_group_pending: dict[int, int] = {}
# Admin qo'shish: owner ID kiritadi (Adminlar → Qo'shish)
_admin_add_awaiting: set[int] = set()
# Leadga javob: admin reply text kiritadi
_lead_reply_pending: dict[int, int] = {}
# Lead ro'yxati konteksti (inline leads)
_lead_list_context: set[int] = set()
# Post qo'shish: rasm/video kutiladi, keyin caption va Yakunlash/Bekor
_post_add_waiting_media: set[int] = set()
_post_add_pending: dict[int, dict] = {}  # uid -> {content_type, file_id, caption}
# Post qo'shish: Yakunlashdan keyin vaqt tanlash — {content_type, file_id?, caption?, text?, hour?}
_post_add_confirm_pending: dict[int, dict] = {}
# Postlar tarixi: yuborilgan xabarlar (chat_id, message_id) — refresh da o'chirish uchun
_history_message_ids: dict[int, list[tuple[int, int]]] = {}


class _AdminAddAwaitingFilter(Filter):
    """True when user is in admin-add flow (entering ID)."""

    async def __call__(self, message: Message) -> bool:
        return (message.from_user.id if message.from_user else 0) in _admin_add_awaiting


class _PostAddPendingFilter(Filter):
    """True when user has sent media for new post and is in caption/confirm step."""

    async def __call__(self, message: Message) -> bool:
        return (message.from_user.id if message.from_user else 0) in _post_add_pending


class _PostAddWaitingMediaFilter(Filter):
    """True when user clicked Post qo'shish and is waiting to send photo/video/text."""

    async def __call__(self, message: Message) -> bool:
        return (message.from_user.id if message.from_user else 0) in _post_add_waiting_media


def _help_text() -> str:
    return f"{HELP_HEADER}\n\n{HELP_GUIDE}"


@router.message(F.chat.type == "private", F.text == "/help")
@router.message(F.chat.type == "private", F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(
        _help_text(),
        reply_markup=admin_main_inline_keyboard(),
    )


# ---------- Post qo'shish tugmasi ----------
@router.message(F.chat.type == "private", F.text == BTN_ADD_POST)
async def btn_add_post(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _post_add_waiting_media.add(uid)
    await message.answer(POST_ADD_SEND_MEDIA, reply_markup=_admin_kb(message))


# ---------- Content: photo, video, text ----------
@router.message(F.chat.type == "private", F.photo)
async def admin_save_photo(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _post_add_waiting_media.discard(uid)
    photo = message.photo[-1]
    _post_add_pending[uid] = {
        "content_type": "photo",
        "file_id": photo.file_id,
        "caption": (message.caption or "").strip(),
    }
    await message.answer(POST_ADD_SEND_CAPTION, reply_markup=post_add_confirm_keyboard())


@router.message(F.chat.type == "private", F.video)
async def admin_save_video(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _post_add_waiting_media.discard(uid)
    _post_add_pending[uid] = {
        "content_type": "video",
        "file_id": message.video.file_id,
        "caption": (message.caption or "").strip(),
    }
    await message.answer(POST_ADD_SEND_CAPTION, reply_markup=post_add_confirm_keyboard())


@router.message(F.chat.type == "private", F.text, _PostAddPendingFilter())
async def admin_post_add_caption(message: Message) -> None:
    """Post qo'shish: caption matnini qabul qilish."""
    uid = message.from_user.id if message.from_user else 0
    if uid not in _post_add_pending:
        return
    _post_add_pending[uid]["caption"] = (message.text or "").strip()
    await message.answer(POST_ADD_CAPTION_ADDED, reply_markup=post_add_confirm_keyboard())


@router.callback_query(F.data == "confirm_post_add")
async def cb_confirm_post_add(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    data = _post_add_pending.pop(uid, None)
    if not data:
        await callback.answer(POST_ADD_CANCELLED)
        return
    _post_add_confirm_pending[uid] = data
    await callback.answer()
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + POST_ADD_PICK_TIME_HOUR,
        reply_markup=post_add_schedule_hour_keyboard(),
    )


@router.callback_query(F.data.regexp(re.compile(r"^post_time_h_(\d+)$")))
async def cb_post_add_hour(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    pending = _post_add_confirm_pending.get(uid)
    if not pending:
        await callback.answer(POST_ADD_CANCELLED)
        return
    match = re.match(r"^post_time_h_(\d+)$", callback.data or "")
    if not match:
        await callback.answer()
        return
    pending["hour"] = int(match.group(1))
    await callback.answer()
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + POST_ADD_PICK_TIME_MINUTE,
        reply_markup=post_add_schedule_minute_keyboard(),
    )


@router.callback_query(F.data.regexp(re.compile(r"^post_time_m_(\d{2})$")))
async def cb_post_add_minute(callback: CallbackQuery) -> None:
    from bot.scheduler import runner as scheduler_runner

    uid = callback.from_user.id if callback.from_user else 0
    pending = _post_add_confirm_pending.pop(uid, None)
    if not pending:
        await callback.answer(POST_ADD_CANCELLED)
        return
    match = re.match(r"^post_time_m_(\d{2})$", callback.data or "")
    if not match:
        await callback.answer()
        return
    minute_str = match.group(1)
    hour = pending.get("hour", 0)
    time_str = schedule_service.parse_time(f"{hour:02d}:{minute_str}") or f"{hour:02d}:{minute_str}"
    if pending.get("content_type") == "text":
        content = await content_service.add_content(
            content_type="text",
            created_by=uid,
            text=pending.get("text") or "",
        )
    else:
        content = await content_service.add_content(
            content_type=pending["content_type"],
            created_by=uid,
            file_id=pending.get("file_id"),
            caption=pending.get("caption") or None,
        )
    schedule_id = await schedule_service.add_schedule(time_str)
    if schedule_id is not None:
        set_ok = await schedule_service.set_schedule_content(schedule_id, content.id)
        if not set_ok:
            logger.warning("Post qo'shishda rejaga content biriktirilmadi: schedule_id=%s, content_id=%s", schedule_id, content.id)
        me = await callback.bot.get_me()
        bot_username = me.username or ""
        job_ok = scheduler_runner.add_schedule_job(callback.bot, bot_username, schedule_id, time_str)
        if not job_ok:
            logger.warning(
                "Post qo'shishda reja job qo'shilmadi: schedule_id=%s, time_str=%s (scheduler ishga tushmagan bo'lishi mumkin)",
                schedule_id, time_str,
            )
    else:
        schedule_id = await schedule_service.get_schedule_id_by_time_str(time_str)
        if schedule_id:
            set_ok = await schedule_service.set_schedule_content(schedule_id, content.id)
            if not set_ok:
                logger.warning("Post qo'shishda mavjud vaqtga content biriktirilmadi: schedule_id=%s, content_id=%s", schedule_id, content.id)
    await callback.answer(POST_ADD_SAVED)
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + CONTENT_SAVED,
        reply_markup=history_delete_keyboard(content.id),
    )


@router.callback_query(F.data == "cancel_post_add")
async def cb_cancel_post_add(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    _post_add_pending.pop(uid, None)
    await callback.answer(POST_ADD_CANCELLED)
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + POST_ADD_CANCELLED,
        reply_markup=None,
    )


@router.callback_query(F.data == "post_time_cancel")
async def cb_post_add_time_cancel(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    _post_add_confirm_pending.pop(uid, None)
    await callback.answer(POST_ADD_CANCELLED)
    await callback.message.edit_text(
        (callback.message.text or "") + "\n\n" + POST_ADD_CANCELLED,
        reply_markup=None,
    )


@router.message(
    F.chat.type == "private",
    F.text,
    ~F.text.startswith("/"),
    F.text.filter(lambda t: t not in _ADMIN_BUTTON_TEXTS),
    _PostAddWaitingMediaFilter(),
)
async def admin_post_add_text(message: Message) -> None:
    """Post qo'shish: faqat matn yuborilganda — pending ga qo'shish, Yakunlash/Bekor ko'rsatish."""
    uid = message.from_user.id if message.from_user else 0
    _post_add_waiting_media.discard(uid)
    text = (message.text or "").strip()
    if not text:
        await message.answer(POST_ADD_SEND_MEDIA, reply_markup=_admin_kb(message))
        return
    _post_add_pending[uid] = {"content_type": "text", "text": text}
    await message.answer(POST_ADD_CAPTION_ADDED, reply_markup=post_add_confirm_keyboard())


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
    content = await content_service.add_content(
        content_type="text",
        created_by=message.from_user.id,
        text=text,
    )
    await message.answer(CONTENT_SAVED, reply_markup=history_delete_keyboard(content.id))


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
    """e.g. /set_times 09:00, 14:00, 18:00 - add times (duplicates skipped). Yangi vaqtlar uchun scheduler job qo'shiladi."""
    from bot.scheduler import runner as scheduler_runner

    match = message.text and re.match(r"^/set_times\s+(.+)$", message.text, re.I)
    if not match:
        return
    raw = match.group(1).strip()
    parts = [p.strip() for p in raw.replace(",", " ").split() if p.strip()]
    added = []
    me = await message.bot.get_me()
    bot_username = me.username or ""
    for p in parts:
        t = schedule_service.parse_time(p)
        if t:
            schedule_id = await schedule_service.add_schedule(t)
            if schedule_id is not None:
                added.append(t)
                scheduler_runner.add_schedule_job(message.bot, bot_username, schedule_id, t)
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


# ---------- History & delete ----------
def _format_posted_at(dt) -> str:
    """Format datetime for 'oxirgi nashr' display."""
    if dt is None:
        return "—"
    if hasattr(dt, "strftime"):
        return dt.strftime("%d.%m.%Y %H:%M")
    return str(dt)


async def _send_history(target):
    """Send history: header + har bir post to'liq (rasm/video/matn) va O'chirish tugmasi."""
    bot = target.bot if isinstance(target, Message) else target.message.bot
    chat_id = target.chat.id if isinstance(target, Message) else target.message.chat.id
    uid = (target.from_user.id if target.from_user else 0) if isinstance(target, Message) else (target.from_user.id if target.from_user else 0)
    for cid, mid in _history_message_ids.get(uid, []):
        try:
            await bot.delete_message(cid, mid)
        except Exception:
            pass
    _history_message_ids[uid] = []
    posts = await content_service.list_content(limit=10, include_deleted=False)
    # Avval qo'shilgan post avval (yuqorida), keyin qo'shilgan keyin
    posts = sorted(posts, key=lambda p: p.id)
    if not posts:
        msg = await bot.send_message(
            chat_id,
            HISTORY_HEADER + "\n(bo'sh)",
            reply_markup=history_refresh_keyboard(),
        )
        _history_message_ids[uid] = [(chat_id, msg.message_id)]
        return
    header_msg = await bot.send_message(
        chat_id,
        HISTORY_HEADER,
        reply_markup=history_refresh_keyboard(),
    )
    message_ids = [(chat_id, header_msg.message_id)]
    for p in posts:
        cap = (p.caption or p.text or "").strip() or ""
        if len(cap) > 1024:
            cap = cap[:1021] + "…"
        try:
            if p.content_type == "photo" and p.file_id:
                m = await bot.send_photo(
                    chat_id, p.file_id, caption=cap, reply_markup=history_delete_keyboard(p.id)
                )
                message_ids.append((chat_id, m.message_id))
            elif p.content_type == "video" and p.file_id:
                m = await bot.send_video(
                    chat_id, p.file_id, caption=cap, reply_markup=history_delete_keyboard(p.id)
                )
                message_ids.append((chat_id, m.message_id))
            elif p.content_type == "text" or (getattr(p, "text", None) and (p.text or "").strip()):
                text = (p.text or p.caption or "").strip() or f"#{p.id}"
                if len(text) > 4096:
                    text = text[:4093] + "…"
                m = await bot.send_message(
                    chat_id, text, reply_markup=history_delete_keyboard(p.id)
                )
                message_ids.append((chat_id, m.message_id))
        except Exception as e:
            logger.exception("History post %s send failed: %s", p.id, e)
    _history_message_ids[uid] = message_ids


@router.message(F.chat.type == "private", F.text == "/history")
@router.message(F.chat.type == "private", F.text == BTN_HISTORY)
async def cmd_history(message: Message) -> None:
    await _send_history(message)


@router.callback_query(F.data == "refresh_history")
async def cb_refresh_history(callback: CallbackQuery) -> None:
    await _send_history(callback)
    await callback.answer("Yangilandi.")


@router.callback_query(F.data.regexp(re.compile(r"^pub_on_(\d+)$")))
async def cb_pub_on(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^pub_on_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    cid = int(match.group(1))
    ok = await content_service.set_content_publishing_enabled(cid, True)
    if ok:
        await callback.answer("Nashr yoqildi.")
        await _send_history(callback)
    else:
        await callback.answer(POST_NOT_FOUND)


@router.callback_query(F.data.regexp(re.compile(r"^pub_off_(\d+)$")))
async def cb_pub_off(callback: CallbackQuery) -> None:
    match = callback.data and re.match(r"^pub_off_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    cid = int(match.group(1))
    ok = await content_service.set_content_publishing_enabled(cid, False)
    if ok:
        await callback.answer("Nashr o'chirildi.")
        await _send_history(callback)
    else:
        await callback.answer(POST_NOT_FOUND)


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
    """Owner: Admin qo'shish — ID va ixtiyoriy username/ism/familiya (masalan: 123456789 @user John Doe)."""
    uid = message.from_user.id if message.from_user else 0
    raw = (message.text or "").strip()
    _admin_add_awaiting.discard(uid)
    parts = raw.split()
    if not parts or not parts[0].isdigit():
        await message.answer(ADMIN_ADD_INVALID_ID, reply_markup=_admin_kb(message))
        return
    telegram_id = int(parts[0])
    username = None
    first_name = None
    last_name = None
    # Optional username as second token (starts with @ or looks like username)
    idx = 1
    if len(parts) > 1 and not parts[1].replace(".", "").isdigit():
        if parts[1].startswith("@"):
            username = parts[1].lstrip("@")
        else:
            # Could be username or first name; if next token exists and starts with @, treat this as first name
            username = parts[1] if len(parts) == 2 or parts[2].startswith("@") else None
            if username is None:
                first_name = parts[1]
        idx = 2
    # Remaining tokens as name
    if first_name is None and len(parts) > idx:
        first_name = parts[idx]
        idx += 1
    if len(parts) > idx:
        last_name = " ".join(parts[idx:])
    if await admin_service.is_admin(telegram_id):
        await message.answer(ADMIN_ALREADY, reply_markup=_admin_kb(message))
        return
    ok = await admin_service.add_admin(telegram_id, username, first_name=first_name, last_name=last_name)
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


async def _build_schedule_content_map(schedules):
    """Build schedule_id -> (content_id, caption_preview) or None."""
    m = {}
    for s in schedules:
        sid = getattr(s, "id", None)
        if sid is None:
            continue
        cid = await schedule_service.get_content_id_for_schedule(sid)
        if cid:
            content = await content_service.get_content_by_id(cid)
            if content and content.status == "active":
                cap = (getattr(content, "caption", None) or getattr(content, "text", None) or f"#{content.id}").strip() or f"#{content.id}"
                m[sid] = (cid, cap[:100])
        if sid not in m:
            m[sid] = None
    return m


def _format_schedule_text(schedules, schedule_content_map):
    """Format schedule message with per-time post info."""
    times_str = ", ".join(s.time_str for s in schedules) if schedules else "—"
    lines = [CURRENT_TIMES.format(times_str), ""]
    for s in schedules:
        info = schedule_content_map.get(getattr(s, "id", None))
        if info:
            cid, preview = info
            line = f"  {s.time_str} — Post #{cid}: {preview[:50]}{'…' if len(preview) > 50 else ''}"
        else:
            line = f"  {s.time_str} — {POST_NOT_ASSIGNED}"
        lines.append(line)
    lines.extend(["", SCHEDULE_ADD_TIME_HINT])
    return "\n".join(lines)


@router.message(F.chat.type == "private", F.text == BTN_SCHEDULE)
async def btn_schedule(message: Message) -> None:
    schedules = await schedule_service.list_schedules()
    schedule_content_map = await _build_schedule_content_map(schedules)
    text = _format_schedule_text(schedules, schedule_content_map)
    await message.answer(text, reply_markup=schedule_keyboard_with_posts(schedules, schedule_content_map))


async def _send_schedule_message(target, reply_markup=None):
    """Send or edit schedule list (for message or callback)."""
    schedules = await schedule_service.list_schedules()
    schedule_content_map = await _build_schedule_content_map(schedules)
    text = _format_schedule_text(schedules, schedule_content_map)
    kb = schedule_keyboard_with_posts(schedules, schedule_content_map) if reply_markup is None else reply_markup
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.regexp(re.compile(r"^del_time_(.+)$")))
async def cb_del_time(callback: CallbackQuery) -> None:
    """Vaqtni o'chirish: del_time_09_00 -> 09:00. Scheduler dan ham job o'chiriladi."""
    from bot.scheduler import runner as scheduler_runner

    match = callback.data and re.match(r"^del_time_(.+)$", callback.data)
    if not match:
        await callback.answer()
        return
    time_encoded = match.group(1)
    time_str = time_encoded.replace("_", ":", 1)
    schedule_id = await schedule_service.get_schedule_id_by_time_str(time_str)
    ok = await schedule_service.remove_schedule(time_str)
    if ok:
        if schedule_id is not None:
            scheduler_runner.remove_schedule_job(schedule_id)
        await callback.answer(SCHEDULE_REMOVED.format(time_str))
        await _send_schedule_message(callback)
    else:
        await callback.answer(SCHEDULE_INVALID)


@router.callback_query(F.data == "schedule_back")
async def cb_schedule_back(callback: CallbackQuery) -> None:
    await _send_schedule_message(callback)
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^assign_post_(\d+)$")))
async def cb_assign_post(callback: CallbackQuery) -> None:
    """Show post list to assign to this schedule time."""
    match = callback.data and re.match(r"^assign_post_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    schedule_id = int(match.group(1))
    # Only allow active posts to be assigned to schedules
    posts = await content_service.list_content(limit=20, include_deleted=False)
    if not posts:
        await callback.answer("Postlar yo'q. Avval post qo'shing.")
        return
    await callback.message.edit_text(
        SCHEDULE_PICK_POST_HEADER,
        reply_markup=schedule_pick_post_keyboard(schedule_id, posts),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^assign_schedule_(\d+)_content_(\d+)$")))
async def cb_assign_schedule_content(callback: CallbackQuery) -> None:
    """Assign post to schedule time."""
    match = callback.data and re.match(r"^assign_schedule_(\d+)_content_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    schedule_id, content_id = int(match.group(1)), int(match.group(2))
    ok = await schedule_service.set_schedule_content(schedule_id, content_id)
    if ok:
        await callback.answer(SCHEDULE_ASSIGNED)
        await _send_schedule_message(callback)
    else:
        await callback.answer("Xatolik.")


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
    from bot.scheduler import runner as scheduler_runner

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
    time_str = schedule_service.parse_time(f"{hour:02d}:{minute_str}") or f"{hour:02d}:{minute_str}"
    schedule_id = await schedule_service.add_schedule(time_str)
    if schedule_id is not None:
        me = await callback.bot.get_me()
        bot_username = me.username or ""
        job_ok = scheduler_runner.add_schedule_job(callback.bot, bot_username, schedule_id, time_str)
        if not job_ok:
            logger.warning(
                "Post vaqtlari: yangi vaqt uchun job qo'shilmadi: schedule_id=%s, time_str=%s",
                schedule_id, time_str,
            )
        await callback.answer(SCHEDULE_TIME_ADDED)
        await _send_schedule_message(callback)
    else:
        await callback.answer(SCHEDULE_INVALID)


@router.callback_query(F.data == "inline_history")
async def cb_inline_history(callback: CallbackQuery) -> None:
    await _send_history(callback)
    await callback.answer()


@router.callback_query(F.data == "inline_schedule")
async def cb_inline_schedule(callback: CallbackQuery) -> None:
    await _send_schedule_message(callback)
    await callback.answer()


@router.callback_query(F.data == "inline_leads")
async def cb_inline_leads(callback: CallbackQuery) -> None:
    """Show unanswered leads list."""
    leads = await leads_service.list_unanswered_leads(limit=20)
    _lead_list_context.add(callback.from_user.id if callback.from_user else 0)
    if not leads:
        await callback.message.edit_text("Javob berilmagan leadlar yo'q.", reply_markup=admin_main_inline_keyboard())
        await callback.answer()
        return
    kb = leads_list_keyboard(leads)
    lines = ["Javob berilmagan leadlar:"]
    for ld in leads:
        lines.append(f"#{ld.id} | user_id: {ld.telegram_user_id} | {ld.created_at}")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "nav_home")
async def cb_nav_home(callback: CallbackQuery) -> None:
    # Admin/owner uchun bosh menyu: inline asosiy keyboard bilan /help matni
    await callback.message.edit_text(
        _help_text(),
        reply_markup=admin_main_inline_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.regexp(re.compile(r"^reply_lead_(\d+)$")))
async def cb_reply_lead(callback: CallbackQuery) -> None:
    """Admin leadga javob bermoqchi — reply matni kutiladi."""
    match = callback.data and re.match(r"^reply_lead_(\d+)$", callback.data)
    if not match:
        await callback.answer()
        return
    lead_id = int(match.group(1))
    uid = callback.from_user.id if callback.from_user else 0
    _lead_reply_pending[uid] = lead_id
    await callback.message.answer(f"Lead #{lead_id} ga javob matnini yuboring.")
    await callback.answer()


@router.message(
    F.chat.type == "private",
    F.text,
    F.text.len() > 0,
    F.text.filter(lambda t: t not in _REPLY_IGNORE_TEXTS),
)
async def admin_reply_to_lead_text(message: Message) -> None:
    """Agar admin leadga javob kiritayotgan bo'lsa, foydalanuvchiga yuborish."""
    uid = message.from_user.id if message.from_user else 0
    if uid not in _lead_reply_pending:
        return
    lead_id = _lead_reply_pending.pop(uid, None)
    if not lead_id:
        return
    lead = await leads_service.get_lead(lead_id)
    if not lead:
        await message.answer("Lead topilmadi.")
        return
    try:
        await message.bot.send_message(lead.telegram_user_id, message.text)
        # lead statusini 'taken' (agar pending bo'lsa) va answered qilib belgilash
        await leads_service.mark_lead_answered(lead_id, uid)
        await message.answer(f"Javob yuborildi. Lead #{lead_id} yopildi.")
    except Exception:
        await message.answer("Javob yuborib bo'lmadi.")
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
    current = await settings_service.get_admin_group_id()
    info = f"Joriy lead guruhi: {current}" if current else "Lead guruhi hali belgilanmagan."
    await message.answer(f"{info}\n\n{ADMIN_GROUP_PROMPT_ID}", reply_markup=_admin_kb(message))


@router.callback_query(F.data == "confirm_admin_group")
async def cb_confirm_admin_group(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    gid = _admin_group_pending.pop(uid, None)
    if gid is not None:
        await settings_service.set_admin_group_id(gid)
        await callback.answer(ADMIN_GROUP_SET)
    else:
        await callback.answer()


@router.callback_query(F.data == "cancel_admin_group")
async def cb_cancel_admin_group(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    _admin_group_pending.pop(uid, None)
    _admin_group_awaiting.discard(uid)
    await callback.answer("Bekor qilindi.")


@router.callback_query(F.data == "cancel_admin_add")
async def cb_cancel_admin_add(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    _admin_add_awaiting.discard(uid)
    await callback.answer("Bekor qilindi.")


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
        name = " ".join(filter(None, [getattr(a, "first_name", None), getattr(a, "last_name", None)])) or "—"
        added = getattr(a, "added_at", None)
        added_str = added.strftime("%Y-%m-%d %H:%M") if added else ""
        lines.append(f"• {a.telegram_id} {uname} | {name} | qo'shilgan: {added_str}")
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor", callback_data="cancel_admin_add")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="nav_home")],
    ])
    await callback.message.edit_text(ADMIN_ADD_PROMPT, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_help_remove")
async def cb_admin_help_remove(callback: CallbackQuery) -> None:
    from bot.texts import REPLY_TO_REMOVE_ADMIN

    if not is_owner(callback.from_user.id or 0):
        await callback.answer("Faqat egasi.", show_alert=True)
        return
    await callback.message.edit_text(REPLY_TO_REMOVE_ADMIN, reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="nav_home")],
        ]
    ))
    await callback.answer()
