from datetime import date, datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from bot.utils import safe_tz
from db.models import User, DiaryEntry, WeeklyDigest


async def get_user(session: AsyncSession, tg_id: int) -> User | None:
    """Получить пользователя по telegram_id. Не создаёт нового."""
    stmt = select(User).where(User.telegram_id == tg_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user(session: AsyncSession, tg_id: int, username: str | None = None) -> tuple:
    """Получить существующего или создать нового пользователя."""
    user = await get_user(session, tg_id)
    
    if user is not None:
        if username is not None and user.username != username:
            user.username = username
            # flush() отправляет UPDATE, коммит — в middleware или вызывающем коде
            await session.flush()
            
        return user, False
    
    # SAVEPOINT: при race condition (два INSERT одного telegram_id)
    # откатывается только вложенная транзакция, основная остаётся рабочей.
    try:
        async with session.begin_nested():
            new_user = User(telegram_id=tg_id, username=username)
            session.add(new_user)
            await session.flush()
        return new_user, True
    except IntegrityError:
        user = await get_user(session, tg_id)
        if user is None:
            raise
        return user, False

async def get_all_users(session: AsyncSession) -> list[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    return result.scalars().all()


async def add_diary_entry(session: AsyncSession, tg_id: int, user_text: str, conversation_log: str | None = None) -> DiaryEntry:
    """Создать запись дневника. flush() — для получения ID, коммит в middleware."""
    user, _ = await get_or_create_user(session, tg_id)
    new_entry = DiaryEntry(
        user_id=user.id, 
        user_text=user_text,
        conversation_log=conversation_log,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None)  # Бронебойный UTC
    )
    session.add(new_entry)
    await session.flush()
    return new_entry


async def get_user_entries(
    session: AsyncSession, 
    tg_id: int, 
    order: str = "asc",
    limit: int | None = None
) -> list[DiaryEntry]:
    """
    Получить записи дневника пользователя.
    order: "asc" (старые первые) или "desc" (новые первые).
    limit: ограничить количество записей.
    """
    ordering = DiaryEntry.created_at.asc() if order == "asc" else DiaryEntry.created_at.desc()
    
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == tg_id)
        .order_by(ordering)
    )
    
    if limit:
        stmt = stmt.limit(limit)
    
    result = await session.execute(stmt)
    return result.scalars().all()


async def check_today_entry(session: AsyncSession, tg_id: int, tz_str: str = "UTC") -> bool:
    """Проверить, есть ли запись за сегодня (с учётом таймзоны юзера).
    Границы дня вычисляются в его таймзоне и конвертируются в UTC для SQL.
    """
    from zoneinfo import ZoneInfo
    user_tz = safe_tz(tz_str)
    now_local = datetime.now(user_tz)
    day_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end_local = day_start_local + timedelta(days=1)
    
    day_start_utc = day_start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    day_end_utc = day_end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    
    stmt = (
        select(DiaryEntry)
        .join(User)
        .where(
            User.telegram_id == tg_id,
            DiaryEntry.created_at >= day_start_utc,
            DiaryEntry.created_at < day_end_utc,
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None  # <--- Добавил _one_


async def update_user_timezone(session: AsyncSession, tg_id: int, new_tz: str) -> User:
    """Обновить таймзону пользователя. Создаёт юзера, если не найден."""
    user, _ = await get_or_create_user(session, tg_id)
    user.timezone = new_tz
    await session.flush()
    return user


async def update_user_time(session: AsyncSession, tg_id: int, new_time: str) -> User:
    """Обновить время напоминания. Создаёт юзера, если не найден."""
    user, _ = await get_or_create_user(session, tg_id)
    user.reminder_time = new_time
    await session.flush()
    return user


async def update_user_language(session: AsyncSession, tg_id: int, lang: str) -> User:
    """Обновить язык интерфейса. Допустимые значения: 'ru', 'en'."""
    user, _ = await get_or_create_user(session, tg_id)
    if user.language_code != lang:
        user.language_code = lang
        # Сбрасываем кэш инсайтов, чтобы теги сгенерировались на новом языке
        user.cached_insights = None
    await session.flush()
    return user


async def update_diary_metrics(session: AsyncSession, entry_id: int, metrics_json: str) -> None:
    """Обновить AI-метрики записи. Коммит — в middleware или явно в вызывающем коде."""
    stmt = update(DiaryEntry).where(DiaryEntry.id == entry_id).values(ai_metrics=metrics_json)
    await session.execute(stmt)
    await session.flush()


async def get_entry_count(session: AsyncSession, tg_id: int) -> int:
    """Получить общее количество записей пользователя (без загрузки всех объектов)."""
    stmt = (
        select(func.count(DiaryEntry.id))
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == tg_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_last_week_entries(session: AsyncSession, tg_id: int, tz_str: str = "UTC") -> list[DiaryEntry]:
    """Записи за прошлую неделю. Границы — в таймзоне юзера, конвертированы в UTC."""
    from zoneinfo import ZoneInfo
    user_tz = safe_tz(tz_str)
    now_local = datetime.now(user_tz)
    today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    
    this_monday_local = today_local - timedelta(days=today_local.weekday())
    last_monday_local = this_monday_local - timedelta(days=7)
    
    last_monday_utc = last_monday_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    this_monday_utc = this_monday_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == tg_id)
        .where(DiaryEntry.created_at >= last_monday_utc)
        .where(DiaryEntry.created_at < this_monday_utc)
        .order_by(DiaryEntry.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_latest_diary_entry(session: AsyncSession, telegram_id: int) -> DiaryEntry | None:
    """Достает самую последнюю запись юзера."""
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == telegram_id)
        .order_by(DiaryEntry.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_adjacent_entry(
    session: AsyncSession, 
    telegram_id: int, 
    current_id: int, 
    direction: str
) -> DiaryEntry | None:
    """Ищет соседнюю запись: старше (prev) или новее (next)."""
    if direction == "prev":
        stmt = (
            select(DiaryEntry)
            .join(User, DiaryEntry.user_id == User.id)
            .where(User.telegram_id == telegram_id, DiaryEntry.id < current_id)
            .order_by(DiaryEntry.id.desc())
            .limit(1)
        )
    else:
        stmt = (
            select(DiaryEntry)
            .join(User, DiaryEntry.user_id == User.id)
            .where(User.telegram_id == telegram_id, DiaryEntry.id > current_id)
            .order_by(DiaryEntry.id.asc())
            .limit(1)
        )
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_digest_day(session: AsyncSession, tg_id: int, day_idx: int) -> User:
    """Обновить день дайджеста. Создаёт юзера, если не найден."""
    user, _ = await get_or_create_user(session, tg_id)
    user.digest_day = day_idx
    await session.flush()
    return user

async def update_user_digest_time(session: AsyncSession, tg_id: int, time_idx: int) -> User:
    """Обновить время дайджеста. Создаёт юзера, если не найден."""
    user, _ = await get_or_create_user(session, tg_id)
    user.digest_time = time_idx
    await session.flush()
    return user


async def add_weekly_digest(session: AsyncSession, tg_id: int, content: str) -> WeeklyDigest:
    user, _ = await get_or_create_user(session, tg_id)
    new_entry = WeeklyDigest(
        user_id=user.id,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        content=content
    )
    session.add(new_entry)
    await session.flush()
    return new_entry


async def get_user_digest(
    session: AsyncSession,
    tg_id: int,
    order: str = "desc",
    limit: int | None = None,
) -> list[WeeklyDigest]:
    
    ordering = WeeklyDigest.created_at.desc() if order == "desc" else WeeklyDigest.created_at.asc()
    
    stmt = (
        select(WeeklyDigest)
        .join(User, WeeklyDigest.user_id == User.id)
        .where(User.telegram_id == tg_id)
        .order_by(ordering)
    )
    
    if limit:
        stmt = stmt.limit(limit)
        
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_entries_by_date_range(
    session: AsyncSession,
    tg_id: int,
    start_date: datetime,
    end_date: datetime
) -> list[DiaryEntry]:
    """Получить записи пользователя за конкретный период дат (в UTC)."""
    
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == tg_id)
        .where(DiaryEntry.created_at >= start_date)
        .where(DiaryEntry.created_at < end_date)
        .order_by(DiaryEntry.created_at.asc())
    )
    
    result = await session.execute(stmt)
    return list(result.scalars().all())