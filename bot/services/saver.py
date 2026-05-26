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

# FIX: CRIT-04 — Двойная стратегия управления сессиями:
# 1) Из хендлера (session передан) — используем middleware-сессию, чтобы не плодить
#    параллельные подключения и сохранить атомарность транзакции хендлера.
# 2) Из scheduler (session=None) — открываем standalone-сессию с явным commit/rollback,
#    т.к. scheduler работает вне контекста middleware.
async def finalize_diary_entry(
    bot: Bot, 
    chat_id: int, 
    user_id: int, 
    text: str, 
    state: FSMContext = None, 
    session: AsyncSession = None
):
    if session:
        # Хендлер передал middleware-сессию — flush произойдёт в add_diary_entry,
        # а финальный commit сделает middleware после завершения хендлера.
        new_entry = await add_diary_entry(session, user_id, text)
    else:
        # Вызов из scheduler/night_cleaner — middleware здесь нет,
        # поэтому открываем свою сессию и сами управляем транзакцией.
        async with async_session() as standalone_session:
            try:
                new_entry = await add_diary_entry(standalone_session, user_id, text)
                await standalone_session.commit()
            except Exception:
                await standalone_session.rollback()
                raise
    
    # Чистим стейт FSM, если он передан (для живых диалогов)
    if state:
        await state.clear()
        
    # Запускаем ИИ-анализ в фоне — он откроет собственную сессию в analytics.py,
    # т.к. может работать минутами и не должен блокировать ответ юзеру.
    task = asyncio.create_task(generate_and_save_metrics(bot, chat_id, new_entry.id, text))
    _background_tasks.add(task)
    task.add_done_callback(_task_done_callback)
    
    return new_entry


# FIX: CQ-05 — Graceful shutdown: отмена всех фоновых AI-задач при остановке бота.
# Без этого при shutdown фоновые задачи могут пытаться писать в уже закрытую БД/сессию,
# вызывая OperationalError и замусоривая логи трейсбеками.
async def cancel_background_tasks() -> None:
    """Отменить все фоновые задачи и дождаться их завершения.
    Вызывается из on_shutdown в main.py перед закрытием engine.
    """
    if not _background_tasks:
        return
    
    logger.info("Отмена {} фоновых задач", len(_background_tasks))
    for task in _background_tasks:
        task.cancel()
    
    # Ждём завершения всех задач (cancelled или finished), подавляя CancelledError
    await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()
    logger.info("Все фоновые задачи завершены")