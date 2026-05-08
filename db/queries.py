from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError  # FIX: CRIT-02
from db.models import User, DiaryEntry


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
            # FIX: CRIT-03 — flush() отправляет UPDATE в БД, но не коммитит.
            # Финальный commit сделает middleware (для хендлеров) или вызывающий код (для scheduler).
            await session.flush()
            
        return user, False
    
    # FIX: CRIT-02 — Защита от race condition при параллельных запросах.
    # Проблема: два запроса могут одновременно пройти get_user() → None и оба попытаться
    # вставить юзера с тем же telegram_id, получив UniqueViolationError.
    # Решение: begin_nested() создаёт SAVEPOINT в PostgreSQL. Если INSERT упадёт
    # с IntegrityError, откатится только savepoint, а основная транзакция останется рабочей.
    # После отката просто достаём уже созданного юзера повторным SELECT.
    try:
        async with session.begin_nested():
            new_user = User(telegram_id=tg_id, username=username)
            session.add(new_user)
            await session.flush()
        return new_user, True
    except IntegrityError:
        # Параллельный INSERT уже создал юзера — savepoint откатился, сессия чистая
        user = await get_user(session, tg_id)
        if user is None:
            raise  # Теоретически невозможно, но перестраховка
        return user, False

async def get_all_users(session: AsyncSession) -> list[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    return result.scalars().all()


async def add_diary_entry(session: AsyncSession, tg_id: int, user_text: str) -> DiaryEntry:
    user, _ = await get_or_create_user(session, tg_id)
    new_entry = DiaryEntry(user_id=user.id, user_text=user_text)
    session.add(new_entry)
    # FIX: CRIT-03 — flush() вместо commit(): запись получит ID из БД (через RETURNING),
    # но транзакция останется открытой до коммита в middleware.
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
    """FIX: BL-03 — Проверка «писал ли юзер сегодня» с учётом его таймзоны.
    
    Проблема: created_at хранится в UTC, а «сегодня» для юзера в Asia/Kamchatka (UTC+12)
    начинается в 12:00 UTC предыдущего дня. Если сравнивать просто func.date(created_at)
    с локальным today, получим несовпадение дат.
    
    Решение: вычисляем границы «сегодня» в таймзоне юзера (00:00 — 23:59:59),
    конвертируем их в UTC, и ищем записи в этом UTC-диапазоне.
    """
    user_tz = ZoneInfo(tz_str)
    # Вычисляем «сегодня 00:00» в таймзоне юзера
    now_local = datetime.now(user_tz)
    day_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end_local = day_start_local + timedelta(days=1)
    
    # Переводим границы в UTC для сравнения с created_at (которое хранится в UTC)
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
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def update_user_timezone(session: AsyncSession, tg_id: int, new_tz: str) -> User:
    """Обновить таймзону пользователя. Создаёт юзера, если не найден."""
    user, _ = await get_or_create_user(session, tg_id)
    user.timezone = new_tz
    await session.flush()  # FIX: CRIT-03 — изменение зафиксируется при коммите в middleware
    return user


async def update_user_time(session: AsyncSession, tg_id: int, new_time: str) -> User:
    """Обновить время напоминания. Создаёт юзера, если не найден."""
    user, _ = await get_or_create_user(session, tg_id)
    user.reminder_time = new_time
    await session.flush()  # FIX: CRIT-03 — аналогично, коммит на уровне middleware
    return user


async def update_diary_metrics(session: AsyncSession, entry_id: int, metrics_json: str) -> None:
    stmt = update(DiaryEntry).where(DiaryEntry.id == entry_id).values(ai_metrics=metrics_json)
    await session.execute(stmt)
    # FIX: CRIT-03 — flush() гарантирует отправку UPDATE в БД.
    # Для вызова из analytics.py (фоновая задача) коммит делается там явно.
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
    """FIX: BL-04 — Границы недели вычисляются в таймзоне юзера, а не сервера.
    
    Проблема: date.today() возвращало серверную дату, а created_at хранится в UTC.
    Для юзера в UTC+12 «прошлая неделя» по серверному UTC — не его реальная неделя.
    
    Решение: вычисляем понедельники в таймзоне юзера, конвертируем в UTC для SQL.
    """
    user_tz = ZoneInfo(tz_str)
    now_local = datetime.now(user_tz)
    today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Понедельник текущей и прошлой недели в локальном времени юзера
    this_monday_local = today_local - timedelta(days=today_local.weekday())
    last_monday_local = this_monday_local - timedelta(days=7)
    
    # Переводим в UTC для сравнения с created_at в БД
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