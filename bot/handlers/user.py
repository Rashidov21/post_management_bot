# -*- coding: utf-8 -*-
"""
User-facing handlers: /start, adminlar ro'yxati, private messages as leads (rate limit).
Oddiy user: guruhdagi post ostidagi tugma orqali botga keladi, faqat Adminlar ro'yxati tugmasi, yozgan xabari lead guruhiga tushadi.
"""
import html
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, CommandObject, Filter

from config import LEAD_RATE_LIMIT_PER_HOUR, is_owner
from bot.texts import (
    WELCOME,
    WELCOME_USER_ONLY_VIA_GROUP,
    LEAD_RATE_LIMIT,
    BTN_USER_ADMINS,
    USER_CONTACT_RECEIVED,
    USER_ADMINS_LIST_HEADER,
    BTN_HELP,
    BTN_HISTORY,
    BTN_POST_ON,
    BTN_POST_OFF,
    BTN_ADD_POST,
    BTN_SCHEDULE,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
    BTN_ADMINS,
)
from bot.services import user_service, leads_service, settings_service, admin_service
from bot.keyboards.reply import user_main_keyboard, admin_main_keyboard

logger = logging.getLogger(__name__)
router = Router(name="user")

# Admin/owner reply keyboard texts — lead handler must not consume these (let admin router handle)
_ADMIN_OWNER_BUTTONS = frozenset({
    BTN_HELP,
    BTN_HISTORY,
    BTN_ADD_POST,
    BTN_POST_ON,
    BTN_POST_OFF,
    BTN_SCHEDULE,
    BTN_TARGET_GROUP,
    BTN_LEAD_GROUP,
    BTN_ADMINS,
    BTN_USER_ADMINS,
})

# In-memory: telegram_id -> content_id (set when user opens bot via post link)
_lead_source_by_user: dict[int, int] = {}
# In-memory: telegram_id -> phone_number (set when user shares contact before sending lead)
_user_phone_for_lead: dict[int, str] = {}


class _NotAdminOrOwnerFilter(Filter):
    """Let only non-admin, non-owner private text reach this handler; admin/owner text goes to admin router."""

    async def __call__(self, message: Message) -> bool:
        uid = message.from_user.id if message.from_user else 0
        if is_owner(uid):
            return False
        return not await admin_service.is_admin(uid)


@router.message(CommandStart(deep_link=True))
async def cmd_start_deep(message: Message, command: CommandObject = None) -> None:
    """Start with optional ?start=post_123 — user yaratiladi, post link bo'lsa lead saqlanadi va lead guruhiga yuboriladi."""
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    cid = None
    if command and command.args and command.args.startswith("post_"):
        try:
            cid = int(command.args.split("_", 1)[1])
            if cid > 0:
                _lead_source_by_user[message.from_user.id] = cid
        except (IndexError, ValueError):
            pass
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    is_admin_user = await admin_service.is_admin(uid)
    # Post ostidagi tugmani bosgan oddiy user: darhol lead qilib saqlash va lead guruhiga yuborish
    if not user_is_owner and not is_admin_user and cid is not None and cid > 0:
        from bot.texts import LEAD_FORWARD_TEMPLATE, LEAD_SOURCE_UNKNOWN, LEAD_CLICKED_BUTTON_TEXT
        from bot.keyboards.inline import lead_actions_keyboard

        lead = await leads_service.create_lead(
            user_id=user.id,
            telegram_user_id=message.from_user.id,
            message_text=LEAD_CLICKED_BUTTON_TEXT,
            source_content_id=cid,
            phone_number=None,
        )
        admin_group_id = await settings_service.get_admin_group_id()
        if admin_group_id:
            name = html.escape((message.from_user.full_name or "—"))
            username = html.escape((message.from_user.username or "—"))
            source_str = f"#{cid}"
            text_escaped = html.escape(LEAD_CLICKED_BUTTON_TEXT)
            forward_text = LEAD_FORWARD_TEMPLATE.format(
                name=name,
                username=username,
                user_id=message.from_user.id,
                phone="—",
                text=text_escaped,
                source=source_str,
            )
            try:
                await message.bot.send_message(
                    chat_id=admin_group_id,
                    text=forward_text,
                    reply_markup=lead_actions_keyboard(
                        lead.id, message.from_user.id, message.from_user.username
                    ),
                )
            except Exception as e:
                logger.exception("Failed to forward post-click lead to admin group: %s", e)
    if user_is_owner or is_admin_user:
        await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=user_is_owner))
    else:
        await message.answer(WELCOME, reply_markup=user_main_keyboard())
        await _send_admin_list_to_user(message)


async def _send_admin_list_to_user(message: Message) -> None:
    """Adminlar ro'yxatini: ID ko'rsatilmasdan, faqat inline Chat tugmalari bilan."""
    admins = await admin_service.list_admins()
    kb_rows = []
    if not admins:
        text = USER_ADMINS_LIST_HEADER + "\n\n(Adminlar ro'yxati hozircha bo'sh.)"
    else:
        text = USER_ADMINS_LIST_HEADER + "\n\nQuyidagi tugmalar orqali chatga o'ting."
        for idx, a in enumerate(admins, start=1):
            name = " ".join(filter(None, [getattr(a, "first_name", None), getattr(a, "last_name", None)])).strip()
            uname = getattr(a, "username", None)
            url = f"https://t.me/{uname}" if uname else f"tg://user?id={a.telegram_id}"
            # ID ko'rsatilmasin — faqat ism yoki @username yoki "Chat"
            label = (name or (f"@{uname}" if uname else f"Admin {idx}"))[:32]
            kb_rows.append([InlineKeyboardButton(text=f"💬 Chat — {label}", url=url)])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None
    await message.answer(text, reply_markup=kb)


async def _send_standard_lead_reply(message: Message) -> None:
    """Oddiy user xabar yozganda: standart javob — xabar qabul qilindi + mahsulot haqida adminlar bilan bog'laning + adminlar ro'yxati (chat tugmalari)."""
    from bot.texts import LEAD_REPLY_STANDARD

    admins = await admin_service.list_admins()
    kb_rows = []
    if not admins:
        text = LEAD_REPLY_STANDARD + "\n\n(Adminlar ro'yxati hozircha bo'sh.)"
    else:
        text = LEAD_REPLY_STANDARD + "\n\nQuyidagi tugmalar orqali chatga o'ting."
        for idx, a in enumerate(admins, start=1):
            name = " ".join(filter(None, [getattr(a, "first_name", None), getattr(a, "last_name", None)])).strip()
            uname = getattr(a, "username", None)
            url = f"https://t.me/{uname}" if uname else f"tg://user?id={a.telegram_id}"
            label = (name or (f"@{uname}" if uname else f"Admin {idx}"))[:32]
            kb_rows.append([InlineKeyboardButton(text=f"💬 Chat — {label}", url=url)])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None
    await message.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Regular /start in private (guruh posti orqali emas)."""
    await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    uid = message.from_user.id if message.from_user else 0
    user_is_owner = is_owner(uid)
    is_admin_user = await admin_service.is_admin(uid)
    if user_is_owner or is_admin_user:
        await message.answer(WELCOME, reply_markup=admin_main_keyboard(include_owner=user_is_owner))
    else:
        await message.answer(WELCOME_USER_ONLY_VIA_GROUP, reply_markup=user_main_keyboard())
        await _send_admin_list_to_user(message)


@router.message(F.chat.type == "private", F.text == BTN_USER_ADMINS, _NotAdminOrOwnerFilter())
async def btn_user_admins(message: Message) -> None:
    """User pressed 'Adminlar ro'yxati' — show admin usernames for contact."""
    await _send_admin_list_to_user(message)


@router.message(F.chat.type == "private", F.contact, _NotAdminOrOwnerFilter())
async def user_contact_for_lead(message: Message) -> None:
    """User shared contact — save phone for next lead message."""
    if message.contact and message.contact.phone_number:
        _user_phone_for_lead[message.from_user.id] = message.contact.phone_number
        await message.answer(USER_CONTACT_RECEIVED)


@router.message(
    F.chat.type == "private",
    F.text,
    ~F.text.startswith("/"),
    F.text.filter(lambda t: t not in _ADMIN_OWNER_BUTTONS),
    _NotAdminOrOwnerFilter(),
)
async def private_message_as_lead(message: Message) -> None:
    """
    Non-command text in private is forwarded to admin group as lead (with rate limit).
    Admin/owner reply button texts are excluded so they reach admin/owner routers.
    """
    source_content_id = _lead_source_by_user.pop(message.from_user.id, None)
    if source_content_id == 0:
        source_content_id = None
    phone = _user_phone_for_lead.pop(message.from_user.id, None)
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )
    # Rate limit
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    count = await leads_service.count_leads_from_user_since(message.from_user.id, since)
    if count >= LEAD_RATE_LIMIT_PER_HOUR:
        await message.answer(LEAD_RATE_LIMIT)
        return
    admin_group_id = await settings_service.get_admin_group_id()
    if not admin_group_id:
        await leads_service.create_lead(
            user_id=user.id,
            telegram_user_id=message.from_user.id,
            message_text=message.text or "",
            source_content_id=source_content_id,
            phone_number=phone,
        )
        await _send_standard_lead_reply(message)
        return
    lead = await leads_service.create_lead(
        user_id=user.id,
        telegram_user_id=message.from_user.id,
        message_text=message.text or "",
        source_content_id=source_content_id,
        phone_number=phone,
    )
    from bot.texts import LEAD_FORWARD_TEMPLATE, LEAD_SOURCE_UNKNOWN, LEAD_SENT_FAILED
    from bot.keyboards.inline import lead_actions_keyboard

    # HTML rejimida yuboriladi — foydalanuvchi matnini escape qilish kerak
    name = html.escape((message.from_user.full_name or "—"))
    username = html.escape((message.from_user.username or "—"))
    source_str = f"#{source_content_id}" if source_content_id else LEAD_SOURCE_UNKNOWN
    phone_str = html.escape(phone or "—")
    text_escaped = html.escape((message.text or "")[:500])
    forward_text = LEAD_FORWARD_TEMPLATE.format(
        name=name,
        username=username,
        user_id=message.from_user.id,
        phone=phone_str,
        text=text_escaped,
        source=source_str,
    )
    try:
        await message.bot.send_message(
            chat_id=admin_group_id,
            text=forward_text,
            reply_markup=lead_actions_keyboard(lead.id, message.from_user.id, message.from_user.username),
        )
        await _send_standard_lead_reply(message)
    except Exception as e:
        logger.exception("Failed to forward lead to admin group: %s", e)
        await _send_standard_lead_reply(message)
