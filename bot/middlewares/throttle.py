"""
Anti-flood middleware: ограничение частоты сообщений на уровне пользователя.
Redis INCR + EXPIRE — атомарный счётчик с TTL.
По умолчанию: максимум 5 сообщений за 10 секунд.
"""

from typing import Any, Awaitable, Callable, Dict
from loguru import logger
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from redis.asyncio import Redis
from config import config
from bot.lexicon.i18n import t

_logger = logger.bind(module="THROTTLE")

RATE_LIMIT = 5
RATE_WINDOW = 10


class ThrottleMiddleware(BaseMiddleware):
    def __init__(self):
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(config.REDIS_URL, decode_responses=True)
        return self._redis

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            is_callback = False
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            is_callback = True
        else:
            return await handler(event, data)

        if user_id is None:
            return await handler(event, data)

        redis = await self._get_redis()
        key = f"throttle:{user_id}"

        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, RATE_WINDOW)

        if current > RATE_LIMIT:
            _logger.warning("Rate limit: user={}, count={}", user_id, current)
            lang = data.get("lang", "ru")
            if is_callback:
                await event.answer(t('common_throttle', lang), show_alert=True)
            else:
                await event.answer(t('common_throttle', lang))
            return

        return await handler(event, data)
