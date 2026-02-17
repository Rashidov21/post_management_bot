# -*- coding: utf-8 -*-
"""
Middleware: allow only admins (or owner) for admin commands.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import OWNER_ID
from bot.services.admin_service import is_admin
from bot.texts import ADMIN_ONLY, OWNER_ONLY


class AdminOnlyMiddleware(BaseMiddleware):
    """Block non-admin messages for handlers that require admin."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        user_id = event.from_user.id if event.from_user else 0
        is_owner = user_id == OWNER_ID
        is_admin_user = await is_admin(user_id)
        if is_owner or is_admin_user:
            data["is_owner"] = is_owner
            data["is_admin"] = True
            return await handler(event, data)
        await event.answer(ADMIN_ONLY)
        return None


class OwnerOnlyMiddleware(BaseMiddleware):
    """Block non-owner for owner-only handlers (e.g. add_admin)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        user_id = event.from_user.id if event.from_user else 0
        if user_id == OWNER_ID:
            data["is_owner"] = True
            return await handler(event, data)
        await event.answer(OWNER_ONLY)
        return None
