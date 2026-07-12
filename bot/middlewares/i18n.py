"""
I18n middleware: инжектирует язык пользователя (lang) в data для всех хендлеров.

Читает language_code из БД через сессию, уже предоставленную DbSessionMiddleware.
Порядок регистрации: ThrottleMiddleware → DbSessionMiddleware → I18nMiddleware.
"""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from db.queries import get_user


class I18nMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        lang = "ru"  # default

        session = data.get("session")
        if session:
            # Извлечь telegram_id из события
            tg_id = self._extract_user_id(event)
            if tg_id:
                user = await get_user(session, tg_id)
                if user:
                    lang = user.language_code or "ru"

        data["lang"] = lang
        return await handler(event, data)

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        """Извлечь telegram_id из Message или CallbackQuery."""
        if isinstance(event, (Message, CallbackQuery)):
            return event.from_user.id if event.from_user else None
        # Для Update — достаём вложенное событие
        if hasattr(event, "message") and event.message and event.message.from_user:
            return event.message.from_user.id
        if hasattr(event, "callback_query") and event.callback_query and event.callback_query.from_user:
            return event.callback_query.from_user.id
        return None
