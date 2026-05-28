from typing import Any, Awaitable, Callable, Dict
from loguru import logger
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db.database import async_session

_logger = logger.bind(module="DB")


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware, который открывает сессию БД для каждого входящего апдейта
    и передаёт её в хендлер через параметр `session`.
    
    Хендлер, которому нужна БД, просто добавляет `session: AsyncSession` в свои аргументы.
    Хендлер, которому БД не нужна, просто не объявляет этот параметр — aiogram его проигнорирует.
    
    Сессия автоматически закрывается после завершения хендлера (через async with).
    
    Unit of Work: query-функции делают flush(), коммит — один раз здесь.
    При ошибке — полный откат всех изменений хендлера.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                # Все query-функции делали flush() — теперь фиксируем транзакцию разом
                await session.commit()
                return result
            except Exception:
                # Откатываем ВСЕ незакоммиченные изменения, чтобы не оставлять «грязные» данные
                await session.rollback()
                _logger.opt(exception=True).error("Транзакция хендлера откачена")
                raise
