"""
Anti-flood middleware: ограничение частоты сообщений на уровне пользователя.
Redis INCR + EXPIRE — атомарный счётчик с TTL.
По умолчанию: максимум 5 сообщений за 10 секунд.
"""

from typing import Any, Awaitable, Callable, Dict
from loguru import logger
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
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
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        redis = await self._get_redis()
        key = f"throttle:{user_id}"

        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, RATE_WINDOW)

        if current > RATE_LIMIT:
            _logger.warning("Rate limit: user={}, count={}", user_id, current)
            # lang ещё не доступен (I18n middleware позже), берём из data если есть
            lang = data.get("lang", "ru")
            await event.answer(t('common_throttle', lang))
            return

        return await handler(event, data)
