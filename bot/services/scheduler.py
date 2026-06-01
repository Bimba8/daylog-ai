from loguru import logger
from urllib.parse import urlparse
import asyncio
from zoneinfo import ZoneInfo
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey, BaseStorage  # FIX: CQ-04 — тип для storage
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.base import JobLookupError
from config import config
from db.database import async_session
from db.queries import check_today_entry, get_last_week_entries, get_user, get_all_users
from bot.keyboards.main_kb import get_report_kb
from bot.services.saver import finalize_diary_entry
from bot.services.ai import generate_weekly_digest
from bot.utils.telegram import safe_send

logger = logger.bind(module="SCHEDULER")

# RedisJobStore (db=1) для persistent jobs (daily, digest).
# Ephemeral jobs (nudge, cleaner) — в MemoryJobStore (default).
_parsed_redis = urlparse(config.REDIS_URL)
_redis_jobstore = RedisJobStore(
    host=_parsed_redis.hostname or 'localhost',
    port=_parsed_redis.port or 6379,
    db=1,
    password=_parsed_redis.password,
)

scheduler = AsyncIOScheduler(
    timezone="UTC",
    jobstores={'redis': _redis_jobstore},
)

# Bot не сериализуется в Redis → persistent jobs получают его через get_bot().
_bot_instance: Bot | None = None


def set_bot(bot: Bot):
    """Инициализация ссылки на бот для scheduled jobs."""
    global _bot_instance
    _bot_instance = bot


def get_bot() -> Bot:
    """Получить текущий бот-инстанс. Кидает RuntimeError если бот ещё не инициализирован."""
    if _bot_instance is None:
        raise RuntimeError("Bot not initialized — call set_bot() before scheduler.start()")
    return _bot_instance


# ──────────────────────────────────────────────
# Nudge — ephemeral, MemoryJobStore (default)
# ──────────────────────────────────────────────

async def send_nudge_message(bot: Bot, chat_id: int) -> None:
    await safe_send(
        bot, chat_id,
        text=(
            "👀 <b>Я всё еще жду ответ</b>\n\n"
            "Мы остановились на самом интересном месте. Допиши мысль или отправь «пока», чтобы завершить запись."
        )
    )

def schedule_nudge(bot: Bot, user_id: int, chat_id: int) -> None:
    run_time = datetime.now(timezone.utc) + timedelta(hours=2)

    scheduler.add_job(
        func=send_nudge_message,
        trigger='date',
        run_date=run_time,
        id=f"nudge_{user_id}",
        replace_existing=True,
        kwargs={'bot': bot, 'chat_id': chat_id}
    )

def cancel_nudge(user_id: int) -> None:
    try:
        scheduler.remove_job(job_id=f"nudge_{user_id}")
    except JobLookupError:
        pass


# ──────────────────────────────────────────────
# Daily Reminder — persistent, RedisJobStore
# ──────────────────────────────────────────────

async def send_daily_reminder(user_id: int) -> None:
    """Ежедневное напоминание (если юзер ещё не писал сегодня)."""
    bot = get_bot()
    async with async_session() as session:
        try:
            user = await get_user(session, user_id)
            if not user:
                return
            
            already_written = await check_today_entry(session, user_id, user.timezone)
            if already_written:
                return
        except Exception as e:
            logger.error("Ошибка проверки записи юзера {}: {}", user_id, e)
            return
    
    await safe_send(
        bot, user_id,
        text=(
            "🌙 <b>Время подвести итоги</b>\n\n"
            "Как прошел день? Жми кнопку ниже и вываливай всё как есть."
        ),
        reply_markup=get_report_kb()
    )
        
def schedule_daily_reminder(bot: Bot, user_id: int, time_str: str, tz_str: str) -> None:
    """Запланировать ежедневное напоминание (persistent, Redis)."""
    hour, minute = map(int, time_str.split(":"))
    
    scheduler.add_job(
        func=send_daily_reminder,
        trigger='cron',
        hour=hour,
        minute=minute,
        timezone=tz_str,
        id=f"daily_{user_id}",
        replace_existing=True,
        jobstore='redis',
        kwargs={'user_id': user_id},
    )


# ──────────────────────────────────────────────
# Night Cleaner — ephemeral, MemoryJobStore (default)
# ──────────────────────────────────────────────

async def run_night_cleaner(bot: Bot, storage: BaseStorage, user_id: int, chat_id: int) -> None:
    """Автосохранение зависшего диалога в 3:00 ночи по таймзоне юзера."""
    key = StorageKey(bot_id=bot.id, chat_id=chat_id, user_id=user_id)
    state = FSMContext(storage=storage, key=key)
    
    data = await state.get_data()
    story = data.get("story")
    
    if not story:
        return
    
    try:
        await finalize_diary_entry(
            bot=bot, 
            chat_id=chat_id, 
            user_id=user_id, 
            text=story, 
            state=state
        )
    except Exception as e:
        logger.error("Night cleaner: ошибка сохранения для юзера {}: {}", user_id, e)
        return
    
    await safe_send(
        bot, chat_id,
        text=(
            "💾 <b>Автосохранение сработало</b>\n\n"
            "Диалог завис, поэтому я заботливо закрыл и сохранил твою запись.\n\n"
            "<i>Уже считаю AI-метрики, результаты будут в статистике.</i>"
        )
    )

def schedule_night_cleaner(bot: Bot, storage: BaseStorage, user_id: int, chat_id: int, tz_str: str = "Europe/Moscow") -> None:
    """Одноразовый cleaner на ближайшие 03:00 в таймзоне юзера."""
    from bot.utils import safe_tz
    user_tz = safe_tz(tz_str)
    now_local = datetime.now(user_tz)
    
    # Вычисляем ближайшее 03:00 в таймзоне юзера
    target_local = now_local.replace(hour=3, minute=0, second=0, microsecond=0)
    if target_local <= now_local:
        # Если 03:00 уже прошло сегодня — берём завтрашнее
        target_local += timedelta(days=1)
    
    # Переводим в UTC для scheduler (который работает в UTC)
    target_utc = target_local.astimezone(ZoneInfo("UTC"))
    
    scheduler.add_job(
        func=run_night_cleaner,
        trigger='date',
        run_date=target_utc,
        id=f"cleaner_{user_id}",
        replace_existing=True,
        kwargs={
            'bot': bot,
            'storage': storage,
            'user_id': user_id,
            'chat_id': chat_id
        }
    )
    
def cancel_night_cleaner(user_id: int) -> None:
    try:
        scheduler.remove_job(job_id=f"cleaner_{user_id}")
    except JobLookupError:
        pass


# ──────────────────────────────────────────────
# Weekly Digest — persistent, RedisJobStore
# ──────────────────────────────────────────────

async def _process_single_user_digest(bot: Bot, user_id: int, tz_str: str) -> None:
    """Генерация дайджеста для одного юзера (собственная DB-сессия)."""
    async with async_session() as session:
        entries = await get_last_week_entries(session, user_id, tz_str=tz_str)
        
    if len(entries) < 2:
        return # Слишком мало данных, скипаем тихо или можно отправить уведомление
    
    digest = await generate_weekly_digest(entries)
    if digest:
        await safe_send(bot, user_id, text=digest)


async def run_global_weekly_digest() -> None:
    """Рассылка дайджестов: фильтрация по дню/часу, батчинг по 10 с паузами."""
    logger.info("Фабрика дайджестов запущена")
    bot = get_bot()
    
    async with async_session() as session:
        users = await get_all_users(session)

    target_users = []
    for user in users:
        try:
            now_local = datetime.now(ZoneInfo(user.timezone))
            if now_local.weekday() == user.digest_day and now_local.hour == user.digest_time:
                target_users.append(user)
        except Exception as e:
            logger.error("Скипаем юзера {}, ошибка таймзоны: {}", user.telegram_id, e)
    
    for user in target_users:
        try:
            await _process_single_user_digest(bot, user.telegram_id, user.timezone)
        except Exception as e:
            logger.error("Дайджест не ушел {}: {}", user.telegram_id, e)
            
        # Лимит Gemini 15 RPM -> строго 1 запрос раз в 4.5 секунды
        await asyncio.sleep(4.5)


def schedule_global_weekly_digest() -> None:
    """Регистрация ежечасной проверки дайджестов (persistent, Redis)."""
    scheduler.add_job(
        func=run_global_weekly_digest,
        trigger='cron',
        minute=0,
        timezone='UTC',
        id="global_weekly_digest",
        replace_existing=True,
        jobstore='redis',
    )