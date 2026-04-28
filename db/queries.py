from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from db.models import User, DiaryEntry

# Функция принимает открытую сессию (session) и ID пользователя из Телеграма (tg_id)
async def get_or_create_user(session: AsyncSession, tg_id: int):
    # Формируем запрос на поиск
    # select(User) — "выбери из таблицы пользователей"
    # where(...) — "где колонка telegram_id совпадает с тем, что нам передали"
    stmt = select(User).where(User.telegram_id == tg_id)
    
    # Отправляем запрос в базу (асинхронно, поэтому await)
    result = await session.execute(stmt)
    
    # scalar_one_or_none() — это удобная команда, которая говорит: "Дай мне один объект из ответа. Если база пуста — верни None (Ничего)"
    user = result.scalar_one_or_none()
    
    # Проверяем, нашли ли мы кого-то
    if user is not None:
        return user # Юзер уже есть, просто возвращаем его и заканчиваем функцию
    
    new_user = User(telegram_id=tg_id) # Если дошли сюда, значит юзера в базе нет. Создаем нового! Мы просто создаем объект класса User, как обычный объект в Питоне
    session.add(new_user) # Добавляем его в нашу "корзину покупок" сессии
    await session.commit() # физически сохраняем изменения в базу
    return new_user # Возвращаем новенького пользователя

async def get_all_users(session: AsyncSession):
    stmt = select(User)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return users

async def add_diary_entry(session: AsyncSession, tg_id: int, user_text: str):
    user = await get_or_create_user(session, tg_id)
    new_entry = DiaryEntry(user_id=user.id, user_text=user_text)
    session.add(new_entry)
    await session.commit()
    return new_entry

async def get_user_entries(session: AsyncSession, tg_id: int):
    user = await get_or_create_user(session, tg_id)
    stmt = select(DiaryEntry).where(DiaryEntry.user_id == user.id).order_by(DiaryEntry.created_at)
    result = await session.execute(stmt)
    return result.scalars().all()

async def check_today_entry(session: AsyncSession, tg_id: int):
    today = date.today()
    stmt = select(DiaryEntry).join(User).where(User.telegram_id == tg_id, func.date(DiaryEntry.created_at) == today)
    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()
    return entry is not None # Вернет True (если нашел) или False (если None)

async def update_user_timezone(session: AsyncSession, tg_id: int, new_tz: str):
    stmt = select(User).where(User.telegram_id == tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        user.timezone = new_tz
        await session.commit()
        return user
    
async def update_user_time(session: AsyncSession, tg_id: int, new_time: str):
    stmt = select(User).where(User.telegram_id == tg_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        user.reminder_time = new_time
        await session.commit()
        return user

async def update_diary_metrics(session: AsyncSession, entry_id: int, metrics_json: str):
    stmt = update(DiaryEntry).where(DiaryEntry.id == entry_id).values(ai_metrics = metrics_json)
    result = await session.execute(stmt)
    await session.commit()
    
async def get_all_user_entries(session, tg_id: int):
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == tg_id) # <-- вот правильное название из твоей БД
        .order_by(DiaryEntry.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_last_week_entries(session: AsyncSession, tg_id: int):
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == tg_id)
        .where(DiaryEntry.created_at >= last_monday)
        .where(DiaryEntry.created_at < this_monday)
        .order_by(DiaryEntry.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_latest_diary_entry(session, telegram_id: int):
    # Достает самую последнюю запись юзера
    stmt = (
        select(DiaryEntry)
        .join(User, DiaryEntry.user_id == User.id)
        .where(User.telegram_id == telegram_id)
        .order_by(DiaryEntry.id.desc())
        .limit(1)
    )
    
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_adjacent_entry(session, telegram_id: int, current_id: int, direction: str):
    # Ищет соседнюю запись: старше (prev) или новее (next)
    if direction == "prev":
        # Ищем запись, которая была ДО текущей (ID меньше)
        stmt = (
            select(DiaryEntry)
            .join(User, DiaryEntry.user_id == User.id)
            .where(User.telegram_id == telegram_id, DiaryEntry.id < current_id)
            .order_by(DiaryEntry.id.desc())
            .limit(1)
        )
    else:
        # Ищем запись, которая была ПОСЛЕ текущей (ID больше)
        stmt = (
            select(DiaryEntry)
            .join(User, DiaryEntry.user_id == User.id)
            .where(User.telegram_id == telegram_id, DiaryEntry.id > current_id)
            .order_by(DiaryEntry.id.asc())
            .limit(1)
        )
        
    result = await session.execute(stmt)
    return result.scalar_one_or_none()