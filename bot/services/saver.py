import asyncio
from loguru import logger
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import async_session
from db.queries import add_diary_entry
from bot.services.analytics import generate_and_save_metrics

logger = logger.bind(module="SAVER")

# Множество для хранения ссылок на фоновые задачи, чтобы GC не собрал их раньше времени
_background_tasks: set[asyncio.Task] = set()

def _task_done_callback(task: asyncio.Task):
    _background_tasks.discard(task)
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.opt(exception=exc).error("Фоновая задача AI-метрик упала")

# Двойная стратегия сессий:
# session передан → middleware-сессия (хендлер), session=None → standalone (scheduler).
async def finalize_diary_entry(
    bot: Bot, 
    chat_id: int, 
    user_id: int, 
    text: str,
    conversation_log: str | None = None,
    state: FSMContext = None, 
    session: AsyncSession = None,
    loading_msg_id: int | None = None,
    lang: str = "ru"
):
    """Финализация записи дневника: сохранение в БД + запуск фонового AI-анализа."""
    if session:
        # Middleware-сессия — flush в add_diary_entry, коммит в middleware
        new_entry = await add_diary_entry(session, user_id, user_text=text, conversation_log=conversation_log)
    else:
        # Standalone-сессия (scheduler/night_cleaner) — явный commit/rollback
        async with async_session() as standalone_session:
            try:
                new_entry = await add_diary_entry(standalone_session, user_id, user_text=text, conversation_log=conversation_log)
                await standalone_session.commit()
            except Exception:
                await standalone_session.rollback()
                raise
    
    # Очистка FSM-стейта (для живых диалогов)
    if state:
        await state.clear()
        
    # AI-анализ в фоне — откроет собственную сессию в analytics.py
    task = asyncio.create_task(generate_and_save_metrics(bot, chat_id, new_entry.id, text, loading_msg_id, lang=lang))
    _background_tasks.add(task)
    task.add_done_callback(_task_done_callback)
    
    return new_entry


# Graceful shutdown: отмена фоновых задач до закрытия БД.
async def cancel_background_tasks() -> None:
    """Отменить все фоновые задачи и дождаться их завершения."""
    if not _background_tasks:
        return
    
    logger.info("Отмена {} фоновых задач", len(_background_tasks))
    for task in _background_tasks:
        task.cancel()
    
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()
    logger.info("Все фоновые задачи завершены")