# -*- coding: utf-8 -*-
"""
Admin handlers: content, schedule, history, settings. Excludes owner-only commands.
"""
import logging
import re

from aiogram import Router, F
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter

from bot.texts import (
    HELP_HEADER, HELP_GUIDE,
    ADD_TEXT_EMPTY,
    TIMES_SET, TARGET_GROUP_SET, TARGET_GROUP_PROMPT_ID, TARGET_GROUP_ID_RECEIVED,
    GROUP_ID_SHOULD_BE_NEGATIVE,
    CONTENT_SAVED, POST_DELETED, POST_NOT_FOUND,
    SCHEDULE_ADDED, SCHEDULE_REMOVED, SCHEDULE_INVALID, CURRENT_TIMES,
    SCHEDULE_ADD_TIME_HINT,
    SCHEDULE_PICK_HOUR, SCHEDULE_PICK_MINUTE, SCHEDULE_TIME_ADDED,
    POST_NOT_ASSIGNED, SCHEDULE_PICK_POST_HEADER, SCHEDULE_ASSIGNED, NASHR_TIMES_LABEL,
    POST_NOW_SUCCESS, POST_NOW_FAILED,
    ADMIN_REMOVED, ADMIN_NOT_FOUND,
    ADMIN_ADD_PROMPT, ADMIN_ADD_INVALID_ID,
    POST_ADD_SEND_MEDIA, POST_ADD_SEND_CAPTION, POST_ADD_CAPTION_ADDED,
    POST_ADD_SAVED, POST_ADD_CANCELLED, POST_ADD_ALREADY_PENDING,
    POST_ADD_PICK_TIME_HOUR, POST_ADD_PICK_TIME_MINUTE,
    POST_ADD_USE_BUTTON_HINT,
    TEXT_POST_SEND_PROMPT,
    BTN_ADD_TEXT_POST,
    ADMIN_ONLY,
)
from bot.services import (
    content_service,
    schedule_service,
    settings_service,
    admin_service,
)
from bot.scheduler import posting as posting_module
from bot.texts import (
    BTN_HELP,
    BTN_ADD_POST,
    BTN_TARGET_GROUP,
)
from bot.keyboards.reply import admin_main_keyboard
from bot.keyboards.inline import (
    history_delete_keyboard,
    schedule_keyboard,
    confirm_target_group_keyboard,
    post_add_confirm_keyboard,
    post_add_schedule_hour_keyboard,
    post_add_schedule_minute_keyboard,
    text_post_confirm_keyboard,
    text_post_schedule_hour_keyboard,
    text_post_schedule_minute_keyboard,
    schedule_hour_keyboard,
    schedule_minute_keyboard,
    schedule_pick_post_keyboard,
    admin_main_inline_keyboard,
)
from config import is_owner

logger = logging.getLogger(__name__)

# Reply keyboard tugma matnlari — admin_text_ignored_for_content ularni yutmasin, maxsus handlerlar ishlasin
_ADMIN_BUTTON_TEXTS = frozenset({
    BTN_HELP,
    BTN_ADD_POST,
    BTN_ADD_TEXT_POST,
    BTN_TARGET_GROUP,
})
def _admin_kb(message: Message):
    return admin_main_keyboard(include_owner=is_owner(message.from_user.id or 0))
router = Router(name="admin")

# Vaqt qo'shish: soat tanlang -> minut tanlang -> add_schedule
_schedule_pending: dict[int, dict] = {}
# Nashr guruhi: ID kiritiladi, keyin inline tasdiq
_target_group_awaiting: set[int] = set()
_target_group_pending: dict[int, int] = {}
# Post qo'shish: rasm/video kutiladi, keyin caption va Yakunlash/Bekor
_post_add_waiting_media: set[int] = set()
_post_add_pending: dict[int, dict] = {}  # uid -> {content_type, file_id, caption}
# Post qo'shish: Yakunlashdan keyin vaqt tanlash — {content_type, file_id?, caption?, text?, hour?}
_post_add_confirm_pending: dict[int, dict] = {}
# Matnli post qo'shish — alohida pending (tugma orqali boshlanadi)
_text_post_awaiting: set[int] = set()  # matn kutilmoqda
_text_post_pending: dict[int, dict] = {}  # uid -> {"text": str}
_text_post_confirm_pending: dict[int, dict] = {}  # uid -> {"text": str, "hour": int, "minute": str}


class _InGroupIdFlowFilter(Filter):
    """True when user is entering group ID (target group flow)."""

    async def __call__(self, message: Message) -> bool:
        uid = message.from_user.id if message.from_user else 0
        return uid in _target_group_awaiting


async def handle_admin_text_post(message: Message) -> None:
    """Admin/owner xabar yuborganda barcha matn holatlari shu yerda hal qilinadi."""
    uid = message.from_user.id if message.from_user else 0
    text = (message.text or "").strip()

    # 1. "Matnli post qo'shish" tugmasi bosilgan — matn kiritish kutilmoqda
    if uid in _text_post_awaiting:
        _text_post_awaiting.discard(uid)
        if not text:
            await message.answer(TEXT_POST_SEND_PROMPT, reply_markup=_admin_kb(message))
            return
        _text_post_pending[uid] = {"text": text}
        await message.answer(text, reply_markup=text_post_confirm_keyboard())
        return

    # 2. Rasm/video yuborilgan — caption kiritish kutilmoqda
    if uid in _post_add_pending:
        pending = _post_add_pending[uid]
        if pending.get("content_type") in ("photo", "video"):
            pending["caption"] = text
            await message.answer(POST_ADD_CAPTION_ADDED, reply_markup=post_add_confirm_keyboard())
        else:
            # Matnli post allaqachon bor — Yakunlash yoki Bekor bosish kerak
            await message.answer(POST_ADD_ALREADY_PENDING, reply_markup=post_add_confirm_keyboard())
        return

    # 3. "Post qo'shish" tugmasi bosilgan — rasm/video/matn kutilmoqda, matn keldi
    if uid in _post_add_waiting_media:
        _post_add_waiting_media.discard(uid)
        if not text:
            await message.answer(POST_ADD_SEND_MEDIA, reply_markup=_admin_kb(message))
            return
        _post_add_pending[uid] = {"content_type": "text", "text": text}
        await message.answer(text, reply_markup=post_add_confirm_keyboard())
        return

    # 4. Hech qanday aktiv flow yo'q — yangi matnli post sifatida qabul qil
    if not text:
        return
    _text_post_pending[uid] = {"text": text}
    await message.answer(text, reply_markup=text_post_confirm_keyboard())


def _help_text() -> str:
    return f"{HELP_HEADER}\n\n{HELP_GUIDE}"


@router.message(F.chat.type == ChatType.PRIVATE, F.text == "/help")
@router.message(F.chat.type == ChatType.PRIVATE, F.text == BTN_HELP)
async def cmd_help(message: Message) -> None:
    await message.answer(
        _help_text(),
        reply_markup=admin_main_inline_keyboard(),
    )


# ---------- Post qo'shish tugmasi ----------
@router.message(F.chat.type == ChatType.PRIVATE, F.text == BTN_ADD_POST)
async def btn_add_post(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _post_add_waiting_media.add(uid)
    await message.answer(POST_ADD_SEND_MEDIA, reply_markup=_admin_kb(message))


# ---------- Matnli post qo'shish (alohida flow) ----------
@router.message(F.chat.type == ChatType.PRIVATE, F.text == BTN_ADD_TEXT_POST)
async def btn_add_text_post(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _text_post_awaiting.add(uid)
    await message.answer(TEXT_POST_SEND_PROMPT, reply_markup=_admin_kb(message))


# ---------- Content: photo, video ----------
@router.message(F.chat.type == ChatType.PRIVATE, F.photo)
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


@router.message(F.chat.type == ChatType.PRIVATE, F.video)
async def admin_save_video(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _post_add_waiting_media.discard(uid)
    _post_add_pending[uid] = {
        "content_type": "video",
        "file_id": message.video.file_id,
        "caption": (message.caption or "").strip(),
    }
    await message.answer(POST_ADD_SEND_CAPTION, reply_markup=post_add_confirm_keyboard())


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
    chat_id = callback.message.chat.id
    await _send_single_post(callback.bot, chat_id, content, uid)
    await callback.answer(POST_ADD_SAVED)
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + CONTENT_SAVED,
            reply_markup=None,
        )
    except Exception:
        pass


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


# ---------- Matnli post: Yakunlash / Bekor / vaqt tanlash ----------
@router.callback_query(F.data == "confirm_text_post_add")
async def cb_confirm_text_post_add(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    data = _text_post_pending.pop(uid, None)
    if not data:
        await callback.answer(POST_ADD_CANCELLED)
        return
    _text_post_confirm_pending[uid] = data
    await callback.answer()
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + POST_ADD_PICK_TIME_HOUR,
            reply_markup=text_post_schedule_hour_keyboard(),
        )
    except Exception:
        await callback.message.answer(
            (callback.message.text or "") + "\n\n" + POST_ADD_PICK_TIME_HOUR,
            reply_markup=text_post_schedule_hour_keyboard(),
        )


@router.callback_query(F.data == "cancel_text_post_add")
async def cb_cancel_text_post_add(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    _text_post_pending.pop(uid, None)
    await callback.answer(POST_ADD_CANCELLED)
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + POST_ADD_CANCELLED,
            reply_markup=None,
        )
    except Exception:
        pass


@router.callback_query(F.data.regexp(re.compile(r"^text_post_h_(\d+)$")))
async def cb_text_post_hour(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    pending = _text_post_confirm_pending.get(uid)
    if not pending:
        await callback.answer(POST_ADD_CANCELLED)
        return
    match = re.match(r"^text_post_h_(\d+)$", callback.data or "")
    if not match:
        await callback.answer()
        return
    pending["hour"] = int(match.group(1))
    await callback.answer()
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + POST_ADD_PICK_TIME_MINUTE,
            reply_markup=text_post_schedule_minute_keyboard(),
        )
    except Exception:
        await callback.message.answer(
            (callback.message.text or "") + "\n\n" + POST_ADD_PICK_TIME_MINUTE,
            reply_markup=text_post_schedule_minute_keyboard(),
        )


@router.callback_query(F.data.regexp(re.compile(r"^text_post_m_(\d{2})$")))
async def cb_text_post_minute(callback: CallbackQuery) -> None:
    from bot.scheduler import runner as scheduler_runner

    uid = callback.from_user.id if callback.from_user else 0
    pending = _text_post_confirm_pending.pop(uid, None)
    if not pending:
        await callback.answer(POST_ADD_CANCELLED)
        return
    match = re.match(r"^text_post_m_(\d{2})$", callback.data or "")
    if not match:
        await callback.answer()
        return
    minute_str = match.group(1)
    hour = pending.get("hour", 0)
    time_str = schedule_service.parse_time(f"{hour:02d}:{minute_str}") or f"{hour:02d}:{minute_str}"
    content = await content_service.add_content(
        content_type="text",
        created_by=uid,
        text=pending.get("text") or "",
    )
    schedule_id = await schedule_service.add_schedule(time_str)
    if schedule_id is not None:
        set_ok = await schedule_service.set_schedule_content(schedule_id, content.id)
        if not set_ok:
            logger.warning("Matnli post qo'shishda rejaga content biriktirilmadi: schedule_id=%s, content_id=%s", schedule_id, content.id)
        me = await callback.bot.get_me()
        bot_username = me.username or ""
        job_ok = scheduler_runner.add_schedule_job(callback.bot, bot_username, schedule_id, time_str)
        if not job_ok:
            logger.warning(
                "Matnli post qo'shishda reja job qo'shilmadi: schedule_id=%s, time_str=%s",
                schedule_id, time_str,
            )
    else:
        schedule_id = await schedule_service.get_schedule_id_by_time_str(time_str)
        if schedule_id:
            set_ok = await schedule_service.set_schedule_content(schedule_id, content.id)
            if not set_ok:
                logger.warning("Matnli post qo'shishda mavjud vaqtga content biriktirilmadi: schedule_id=%s, content_id=%s", schedule_id, content.id)
    chat_id = callback.message.chat.id
    await _send_single_post(callback.bot, chat_id, content, uid)
    await callback.answer(POST_ADD_SAVED)
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + CONTENT_SAVED,
            reply_markup=None,
        )
    except Exception:
        pass


@router.callback_query(F.data == "text_post_time_cancel")
async def cb_text_post_time_cancel(callback: CallbackQuery) -> None:
    uid = callback.from_user.id if callback.from_user else 0
    _text_post_confirm_pending.pop(uid, None)
    await callback.answer(POST_ADD_CANCELLED)
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + "\n\n" + POST_ADD_CANCELLED,
            reply_markup=None,
        )
    except Exception:
        pass


@router.message(F.chat.type == ChatType.PRIVATE, F.text.regexp(re.compile(r"^/add_text\s+(.+)$", re.DOTALL)))
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
    uid = message.from_user.id if message.from_user else 0
    await _send_single_post(message.bot, message.chat.id, content, uid)
    await message.answer(CONTENT_SAVED, reply_markup=_admin_kb(message))


@router.message(F.chat.type == ChatType.PRIVATE, F.text.regexp(re.compile(r"^/add_text\s*$")))
async def admin_add_text_empty(message: Message) -> None:
    """Prompt when /add_text has no body."""
    await message.answer(ADD_TEXT_EMPTY, reply_markup=_admin_kb(message))


@router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text,
    F.text.startswith("/") == False,
    ~F.text.in_(_ADMIN_BUTTON_TEXTS),
    _InGroupIdFlowFilter(),
)
async def admin_text_ignored_for_content(message: Message) -> None:
    """Guruh ID / admin ID kiritish flow'ida yuborilgan matn (post emas) — user router ishlamasligi uchun yutib qolinadi."""
    pass


# ---------- Schedule ----------
@router.message(F.chat.type == ChatType.PRIVATE, F.text.regexp(re.compile(r"^/set_times\s+(.+)$", re.I)))
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


def _cap_or_text(p, max_cap=1024, max_text=4096) -> tuple:
    """Caption (photo/video) yoki to'liq matn (text post) — kesilgan."""
    cap = (p.caption or p.text or "").strip() or ""
    if len(cap) > max_cap:
        cap = cap[: max_cap - 3] + "…"
    text = (p.text or p.caption or "").strip() or f"#{p.id}"
    if len(text) > max_text:
        text = text[: max_text - 3] + "…"
    return cap, text


async def _send_single_post(bot, chat_id: int, content, uid: int) -> None:
    """Bitta postni chatga yuboradi: avval eski admin xabarlarini o'chiradi, keyin yangi yuboradi va DB ga saqlaydi."""
    old_msgs = await content_service.get_admin_messages(content.id)
    for old_chat_id, old_message_id in old_msgs:
        try:
            await bot.delete_message(old_chat_id, old_message_id)
        except Exception:
            pass
    await content_service.delete_admin_messages(content.id)

    cap, text = _cap_or_text(content)
    try:
        m = None
        if content.content_type == "photo" and content.file_id:
            m = await bot.send_photo(
                chat_id, content.file_id, caption=cap,
                parse_mode=None, reply_markup=history_delete_keyboard(content.id)
            )
        elif content.content_type == "video" and content.file_id:
            m = await bot.send_video(
                chat_id, content.file_id, caption=cap,
                parse_mode=None, reply_markup=history_delete_keyboard(content.id)
            )
        elif content.content_type == "text" or (getattr(content, "text", None) and (content.text or "").strip()):
            m = await bot.send_message(
                chat_id, text, parse_mode=None, reply_markup=history_delete_keyboard(content.id)
            )
        if m is not None:
            await content_service.save_admin_message(content.id, uid, chat_id, m.message_id)
    except Exception as e:
        logger.exception("Single post %s send failed: %s", content.id, e)


async def send_all_posts_to_admin(bot, chat_id: int, uid: int) -> None:
    """Admin uchun barcha aktiv postlarni chatga yuboradi (eski xabarlar o'chiriladi)."""
    posts = await content_service.list_content(include_deleted=False)
    posts = sorted(posts, key=lambda p: p.id)
    for p in posts:
        await _send_single_post(bot, chat_id, p, uid)


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
    else:
        await callback.answer(POST_NOT_FOUND)


@router.message(F.chat.type == ChatType.PRIVATE, F.text.regexp(re.compile(r"^/delete_post\s+(\d+)$")))
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
    admin_messages = await content_service.get_admin_messages(cid)
    ok = await content_service.delete_content(cid)
    if ok:
        for chat_id, message_id in admin_messages:
            try:
                await callback.bot.delete_message(chat_id, message_id)
            except Exception:
                pass
        await callback.answer(POST_DELETED)
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
    else:
        await callback.answer(POST_NOW_FAILED)


# ---------- Target group: admin sends /set_target_group in the group ----------
@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), F.text == "/set_target_group")
async def cmd_set_target_group_in_group(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    if not is_owner(uid) and not await admin_service.is_admin(uid):
        await message.answer(ADMIN_ONLY)
        return
    gid = message.chat.id
    await settings_service.set_target_group_id(gid)
    await message.answer(TARGET_GROUP_SET)


@router.message(F.chat.type == ChatType.PRIVATE, F.text.regexp(re.compile(r"^/set_target_group\s+(-?\d+)$")))
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


@router.message(F.chat.type == ChatType.PRIVATE, F.text == "/set_target_group")
@router.message(F.chat.type == ChatType.PRIVATE, F.text == BTN_TARGET_GROUP)
async def cmd_set_target_group_private(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    _target_group_awaiting.add(uid)
    await message.answer(TARGET_GROUP_PROMPT_ID, reply_markup=_admin_kb(message))


@router.message(F.chat.type == ChatType.PRIVATE, F.text.regexp(re.compile(r"^-?\d+$")))
async def admin_text_group_id(message: Message) -> None:
    """Accept target or lead group ID when user is in corresponding awaiting set."""
    uid = message.from_user.id if message.from_user else 0
    gid = int(message.text.strip())
    if uid in _target_group_awaiting:
        _target_group_awaiting.discard(uid)
        _target_group_pending[uid] = gid
        await message.answer(TARGET_GROUP_ID_RECEIVED, reply_markup=confirm_target_group_keyboard())


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


async def _send_schedule_message(callback: CallbackQuery) -> None:
    """Joriy reja vaqtlari va postlarni ko'rsatish; tugmalar orqali boshqarish."""
    schedules = await schedule_service.list_schedules()
    schedule_content_map = await _build_schedule_content_map(schedules)
    text = _format_schedule_text(schedules, schedule_content_map)
    await callback.message.edit_text(text, reply_markup=schedule_keyboard(schedules))


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
    if ok and schedule_id is not None:
        scheduler_runner.remove_schedule_job(schedule_id)
        await callback.answer(SCHEDULE_REMOVED.format(time_str))
    else:
        await callback.answer(SCHEDULE_INVALID)


@router.callback_query(F.data == "schedule_back")
async def cb_schedule_back(callback: CallbackQuery) -> None:
    await cb_nav_home(callback)


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
    await cb_nav_home(callback)


@router.callback_query(F.data == "inline_schedule")
async def cb_inline_schedule(callback: CallbackQuery) -> None:
    await cb_nav_home(callback)


@router.callback_query(F.data == "nav_home")
async def cb_nav_home(callback: CallbackQuery) -> None:
    # Admin/owner uchun bosh menyu: inline asosiy keyboard bilan /help matni
    await callback.message.edit_text(
        _help_text(),
        reply_markup=admin_main_inline_keyboard(),
    )
    await callback.answer()


