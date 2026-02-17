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
    CMD_HISTORY, CMD_DELETE_POST, CMD_SET_BANNER, CMD_SET_TARGET_GROUP, CMD_SET_ADMIN_GROUP,
    POSTING_ON, POSTING_OFF, TIMES_SET, TARGET_GROUP_SET, ADMIN_GROUP_SET, BANNER_SET,
    CONTENT_SAVED, NO_ACTIVE_CONTENT, HISTORY_HEADER, POST_DELETED, POST_NOT_FOUND,
    SCHEDULE_ADDED, SCHEDULE_REMOVED, SCHEDULE_INVALID, CURRENT_TIMES,
)
from bot.services import (
    content_service,
    schedule_service,
    settings_service,
)
from bot.database.models import ContentType
from bot.keyboards.inline import history_delete_keyboard

logger = logging.getLogger(__name__)
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
        CMD_SET_BANNER,
        CMD_SET_TARGET_GROUP,
        CMD_SET_ADMIN_GROUP,
    ])


@router.message(F.chat.type == "private", F.text == "/help")
async def cmd_help(message: Message) -> None:
    await message.answer(_help_text())


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
    await message.answer(CONTENT_SAVED)


@router.message(F.chat.type == "private", F.video)
async def admin_save_video(message: Message) -> None:
    await content_service.add_content(
        content_type="video",
        created_by=message.from_user.id,
        file_id=message.video.file_id,
        caption=message.caption,
    )
    await message.answer(CONTENT_SAVED)


@router.message(F.chat.type == "private", F.text, F.text.startswith("/") == False)
async def admin_text_ignored_for_content(message: Message) -> None:
    """Non-command text from admin in private: treat as lead (handled in user router)."""
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
        await message.answer(TIMES_SET + "\n" + CURRENT_TIMES.format(", ".join(await _format_times())))
    else:
        await message.answer(SCHEDULE_INVALID)


async def _format_times() -> list:
    schedules = await schedule_service.list_schedules()
    return [s.time_str for s in schedules]


@router.message(F.chat.type == "private", F.text == "/post_on")
async def cmd_post_on(message: Message) -> None:
    await settings_service.set_posting_enabled(True)
    await message.answer(POSTING_ON)


@router.message(F.chat.type == "private", F.text == "/post_off")
async def cmd_post_off(message: Message) -> None:
    await settings_service.set_posting_enabled(False)
    await message.answer(POSTING_OFF)


# ---------- History & delete ----------
@router.message(F.chat.type == "private", F.text == "/history")
async def cmd_history(message: Message) -> None:
    posts = await content_service.list_all_posts_for_history(limit=20)
    if not posts:
        await message.answer(HISTORY_HEADER + "\n(bo'sh)")
        return
    lines = [HISTORY_HEADER]
    for p in posts:
        status = "✅" if p.status == "active" else "❌"
        lines.append(f"{status} ID: {p.id} | {p.content_type} | {p.created_at}")
    await message.answer("\n".join(lines))


@router.message(F.chat.type == "private", F.text.regexp(re.compile(r"^/delete_post\s+(\d+)$")))
async def cmd_delete_post(message: Message) -> None:
    match = message.text and re.match(r"^/delete_post\s+(\d+)$", message.text)
    if not match:
        return
    cid = int(match.group(1))
    ok = await content_service.delete_content(cid)
    if ok:
        await message.answer(POST_DELETED)
    else:
        await message.answer(POST_NOT_FOUND)


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
    await callback.answer()


# ---------- Banner ----------
@router.message(F.chat.type == "private", F.photo, F.caption.regexp(re.compile(r"^/set_banner", re.I)))
async def admin_set_banner(message: Message) -> None:
    photo = message.photo[-1]
    await settings_service.set_banner_file_id(photo.file_id)
    await message.answer(BANNER_SET)


# ---------- Target group: admin sends /set_target_group in the group ----------
@router.message(F.chat.type.in_({"group", "supergroup"}), F.text == "/set_target_group")
async def cmd_set_target_group_in_group(message: Message) -> None:
    gid = message.chat.id
    await settings_service.set_target_group_id(gid)
    await message.answer(TARGET_GROUP_SET)


@router.message(F.chat.type == "private", F.text == "/set_target_group")
async def cmd_set_target_group_private(message: Message) -> None:
    await message.answer("Nashr guruhida /set_target_group buyrug'ini yuboring.")


@router.message(F.chat.type.in_({"group", "supergroup"}), F.text == "/set_admin_group")
async def cmd_set_admin_group_in_group(message: Message) -> None:
    gid = message.chat.id
    await settings_service.set_admin_group_id(gid)
    await message.answer(ADMIN_GROUP_SET)


@router.message(F.chat.type == "private", F.text == "/set_admin_group")
async def cmd_set_admin_group_private(message: Message) -> None:
    await message.answer("Leadlar yuboriladigan guruhda /set_admin_group buyrug'ini yuboring.")


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
