from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db.database import async_session


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware, который открывает сессию БД для каждого входящего апдейта
    и передаёт её в хендлер через параметр `session`.
    
    Хендлер, которому нужна БД, просто добавляет `session: AsyncSession` в свои аргументы.
    Хендлер, которому БД не нужна, просто не объявляет этот параметр — aiogram его проигнорирует.
    
    Сессия автоматически закрывается после завершения хендлера (через async with).
    
    FIX: CRIT-03 — Реализован паттерн "Unit of Work":
    - Все query-функции теперь делают flush() (отправляют SQL, но НЕ коммитят).
    - Коммит происходит ОДИН раз здесь, после успешного завершения хендлера.
    - При любой ошибке — откат ВСЕХ изменений за один хендлер целиком.
    Это гарантирует атомарность: либо все DB-операции хендлера сохраняются, либо ни одна.
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
                raise
