"""
API Rate Limiter: ограничение частоты запросов на уровне пользователя.
Redis INCR + EXPIRE — атомарный счётчик с TTL.
Идентификация по JWT user_id (из Authorization header).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from redis.asyncio import Redis
from loguru import logger
from config import config
from api.security import decode_jwt_token

_logger = logger.bind(module="API_RATE_LIMIT")

# Глобальные лимиты (запросов за окно)
_DEFAULT_LIMIT = 30
_DEFAULT_WINDOW = 60  # секунд

# Тяжёлые эндпоинты (AI-генерация) — жёстче
_HEAVY_PATHS = {"/api/stats/analytics"}
_HEAVY_LIMIT = 5
_HEAVY_WINDOW = 60


class APIRateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(config.REDIS_URL, decode_responses=True)
        return self._redis

    async def dispatch(self, request: Request, call_next):
        # Пропускаем healthcheck и auth (auth сам себя защищает через initData)
        if request.url.path in ("/health", "/api/auth"):
            return await call_next(request)

        # Достаём user_id из Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header[7:]
        user_id = decode_jwt_token(token)
        if user_id is None:
            return await call_next(request)

        # Определяем лимит для данного пути
        path = request.url.path
        if path in _HEAVY_PATHS:
            limit, window = _HEAVY_LIMIT, _HEAVY_WINDOW
            key = f"api_rl:{user_id}:heavy"
        else:
            limit, window = _DEFAULT_LIMIT, _DEFAULT_WINDOW
            key = f"api_rl:{user_id}:general"

        redis = await self._get_redis()
        current = await redis.incr(key)
        if current == 1:
            await redis.expire(key, window)

        if current > limit:
            _logger.warning("API rate limit: user={}, path={}, count={}", user_id, path, current)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )

        return await call_next(request)
