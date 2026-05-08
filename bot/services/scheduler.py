import logging
from urllib.parse import urlparse
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey, BaseStorage  # FIX: CQ-04 — тип для storage
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.jobstores.base import JobLookupError
from config import config
from db.database import async_session
from db.queries import check_today_entry, get_last_week_entries, get_user
from bot.keyboards.main_kb import get_report_kb
from bot.services.saver import finalize_diary_entry
from bot.services.ai import generate_weekly_digest
from bot.utils.telegram import safe_send

logger = logging.getLogger(__name__)

# FIX: ARCH-01 — RedisJobStore для persistent jobs (daily_reminder, weekly_digest).
# При рестарте бота эти задачи восстанавливаются из Redis автоматически.
# Используем db=1, чтобы не конфликтовать с FSM-хранилищем aiogram (db=0).
# Ephemeral jobs (nudge, night_cleaner) остаются в default MemoryJobStore —
# они привязаны к текущему FSM-сеансу и не нужны после рестарта.
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

# FIX: ARCH-01 — Bot нельзя сериализовать в Redis (он содержит aiohttp-сессии,
# SSL-контексты и прочие несериализуемые объекты).
# Поэтому persistent jobs (хранящиеся в Redis) не получают bot через kwargs.
# Вместо этого они достают его через get_bot() из модульной переменной,
# которая инициализируется один раз при старте бота через set_bot().
_bot_instance: Bot | None = None


def set_bot(bot: Bot):
    """Сохранить ссылку на бот-инстанс для использования в scheduled jobs.
    Вызывается один раз из main.py перед scheduler.start().
    """
    global _bot_instance
    _bot_instance = bot


def get_bot() -> Bot:
    """Получить текущий бот-инстанс. Кидает RuntimeError если бот ещё не инициализирован."""
    if _bot_instance is None:
        raise RuntimeError("Bot not initialized — call set_bot() before scheduler.start()")
    return _bot_instance


# ──────────────────────────────────────────────
# Nudge — ephemeral, MemoryJobStore (default)
# Bot передаётся в kwargs напрямую — он не сериализуется, а хранится в памяти.
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
        # jobstore не указан → default MemoryJobStore
    )

def cancel_nudge(user_id: int) -> None:
    try:
        scheduler.remove_job(job_id=f"nudge_{user_id}")
    except JobLookupError:
        pass


# ──────────────────────────────────────────────
# Daily Reminder — persistent, RedisJobStore
# Переживает рестарт бота. Bot достаётся через get_bot().
# ──────────────────────────────────────────────

async def send_daily_reminder(user_id: int) -> None:
    """Отправить ежедневное напоминание, если юзер ещё не писал сегодня.
    Вызывается scheduler'ом — bot берётся из get_bot(), а не из kwargs,
    потому что эта job хранится в Redis и kwargs должны быть сериализуемыми.
    """
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
            logger.error(f"Ошибка при проверке записи юзера {user_id}: {e}")
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
    """Запланировать ежедневное напоминание в Redis.
    Параметр bot принимается для совместимости с вызовами из хендлеров,
    но НЕ передаётся в kwargs — job-функция достанет его через get_bot().
    """
    hour, minute = map(int, time_str.split(":"))
    
    # FIX: ARCH-01 — jobstore='redis': задача переживёт рестарт бота
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
# Привязан к текущему FSM-сеансу: storage не сериализуется.
# ──────────────────────────────────────────────

async def run_night_cleaner(bot: Bot, storage: BaseStorage, user_id: int, chat_id: int) -> None:
    """Автосохранение зависшего FSM-диалога в 3:00 ночи.
    Создаёт FSM-контекст вручную через StorageKey, достаёт незавершённую историю
    и сохраняет её в БД. Вызывается без middleware — finalize откроет standalone-сессию.
    """
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
        logger.error(f"Night cleaner: ошибка сохранения для юзера {user_id}: {e}")
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
    """FIX: BL-06 — Триггер 'date' вместо 'cron': cleaner срабатывает ОДИН раз
    в ближайшие 03:00 по таймзоне юзера, а не каждую ночь бесконечно.
    
    Проблема с 'cron': если FSM-стейт не очищен (ошибка, сетевой сбой),
    cleaner срабатывал каждую ночь, потенциально дублируя записи.
    С 'date' он сработает ровно один раз — если к тому моменту диалог ещё висит.
    """
    from zoneinfo import ZoneInfo
    user_tz = ZoneInfo(tz_str)
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
        # jobstore не указан → default MemoryJobStore
    )    
    
def cancel_night_cleaner(user_id: int) -> None:
    try:
        scheduler.remove_job(job_id=f"cleaner_{user_id}")
    except JobLookupError:
        pass


# ──────────────────────────────────────────────
# Weekly Digest — persistent, RedisJobStore
# Переживает рестарт. Bot через get_bot().
# ──────────────────────────────────────────────

async def run_weekly_digest(user_id: int) -> None:
    """Сгенерировать и отправить еженедельный AI-дайджест.
    Bot берётся через get_bot() — эта job хранится в Redis.
    """
    bot = get_bot()
    async with async_session() as session:
        try:
            # FIX: BL-04 — Загружаем юзера, чтобы получить его таймзону для корректных границ недели
            user = await get_user(session, user_id)
            if not user:
                return
            entries = await get_last_week_entries(session, user_id, tz_str=user.timezone)
        except Exception as e:
            logger.error(f"Digest: ошибка загрузки записей юзера {user_id}: {e}")
            return
        
        if len(entries) < 2:
            await safe_send(
                bot, user_id,
                text=(
                    "📊 <b>Мало данных для дайджеста</b>\n\n"
                    "На прошлой неделе было слишком мало записей для глубокого анализа от нейросети. Жду твоих подробных историй на этой неделе!"
                )
            )
            return
        
        digest = await generate_weekly_digest(entries)
        
        if not digest:
            await safe_send(
                bot, user_id,
                text=(
                    "⚠️ <b>Дайджест задерживается</b>\n\n"
                    "Сервера ИИ прилегли отдохнуть, поэтому сгенерировать отчет за неделю не вышло. Попробуем в следующий понедельник!"
                )
            )
            return
        
        await safe_send(bot, user_id, text=digest)
    
def schedule_weekly_digest(bot: Bot, user_id: int, tz_str: str = "Europe/Moscow") -> None:
    """Запланировать еженедельный дайджест в Redis.
    Bot НЕ передаётся в kwargs — job-функция достанет его через get_bot().
    """
    # FIX: ARCH-01 — jobstore='redis': задача переживёт рестарт бота
    scheduler.add_job(
        func=run_weekly_digest,
        trigger='cron',
        day_of_week='mon',
        hour=10,
        minute=0,
        timezone=tz_str,
        id=f"digest_{user_id}",
        replace_existing=True,
        jobstore='redis',
        kwargs={'user_id': user_id},
    )