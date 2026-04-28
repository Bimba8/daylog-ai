from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from db.database import async_session
from db.queries import add_diary_entry, check_today_entry, get_last_week_entries
from bot.keyboards.main_kb import get_report_kb
from bot.services.saver import finalize_diary_entry
from bot.services.ai import generate_weekly_digest

scheduler = AsyncIOScheduler(timezone="UTC") # Этот объект scheduler мы потом запускаем в main.py (через scheduler.start()). timezone="UTC" нужно, чтобы избежать багов с системным временем сервера.

async def send_nudge_message(bot: Bot, chat_id: int):
    # Это просто тупая функция отправки сообщения.
    # Планировщик дернет её ровно в тот момент, когда истекут 2 часа.
    await bot.send_message(chat_id=chat_id, text="Эй, я всё еще жду твой ответ! 👀")

def schedule_nudge(bot: Bot, user_id: int, chat_id: int):
    # 1. Вычисляем точное время: "Время прямо сейчас + 2 часа"
    run_time = datetime.now(timezone.utc) + timedelta(hours=2) # через какое время напоминалка hours=2 (тест minutes=1)

    # 2. Добавляем задачу в движок
    scheduler.add_job(
        func=send_nudge_message,                 # Какую функцию дернуть (из Блока 2)
        trigger='date',                          # Тип таймера: date = сработает 1 раз
        run_date=run_time,                       # Когда сработает: переменная со временем
        id=f"nudge_{user_id}",                   # Уникальное имя (чтобы мы могли потом её найти и убить)
        kwargs={'bot': bot, 'chat_id': chat_id}  # Та самая "посылка" с переменными для функции
    )

def cancel_nudge(user_id: int):
    try:
        # Ищем задачу по тому самому уникальному имени из schedule_nudge и удаляем
        scheduler.remove_job(job_id=f"nudge_{user_id}")
    except JobLookupError:
        pass # Ошибка? Задачи нет? Игнорируем (pass)
    
async def send_daily_reminder(bot: Bot, user_id: int):
    # В будущем тут можно будет добавить проверку, не пишет ли юзер прямо сейчас дневник.
    # Но пока просто отправляем стартовый пинг:
    async with async_session() as session:
        already_written = await check_today_entry(session, user_id)
        
        if already_written:
            return
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text="Привет! 🌙 \nПришло время подвести итоги дня. Как всё прошло?",
            reply_markup=get_report_kb()
        )
    except Exception as e:
        print(f"Не удалось отправить напоминание юзеру {user_id}: {e}")
        
def schedule_daily_reminder(bot: Bot, user_id: int, time_str: str, tz_str: str):
    hour, minute = map(int, time_str.split(":"))
    
    scheduler.add_job(
        func=send_daily_reminder,
        trigger='cron',
        hour=hour,
        minute=minute,
        timezone=tz_str,
        id=f"daily_{user_id}",
        replace_existing=True,             # Важная штука: если юзер поменяет время, старый таймер с таким id перезапишется
        kwargs={
            'bot': bot,
            'user_id': user_id
        }
    )
    
async def run_night_cleaner(bot: Bot, storage, user_id: int, chat_id: int):
    # 1. Создаем ключ-отмычку и получаем пульт управления памятью
    key = StorageKey(bot_id=bot.id, chat_id=chat_id, user_id=user_id)
    state = FSMContext(storage=storage, key=key)
    
    # 2. Достаем данные юзера
    data = await state.get_data()
    story = data.get("story")
    
    # Если истории почему-то нет (пусто) — просто уходим, сохранять нечего
    if not story:
        return
    
    # 3. Сохраняем в базу данных (используем твои готовые функции)
    await finalize_diary_entry(
        bot=bot, 
        chat_id=chat_id, 
        user_id=user_id, 
        text=story, 
        state=state
    )
    
    await bot.send_message(
        chat_id=chat_id,
        text="Ты так и не ответил, поэтому я заботливо сохранил твой день в дневник. 🌙\n\n"
             "<i>Уже считаю AI-метрики, утром посмотришь результаты!</i>"
    )

def schedule_night_cleaner(bot: Bot, storage, user_id: int, chat_id: int):
    scheduler.add_job(
        func=run_night_cleaner,
        trigger='cron',
        hour=3,                      # Запуск ровно в 03:00 ночи
        minute=00,
        timezone='Europe/Moscow',
        id=f"cleaner_{user_id}",     # Свой отдельный id для уборщика!
        kwargs={
            'bot': bot,
            'storage': storage,
            'user_id': user_id,
            'chat_id': chat_id
        }
    )    
    
def cancel_night_cleaner(user_id: int):
    try:
        scheduler.remove_job(job_id=f"cleaner_{user_id}")
    except:
        pass
    
async def run_weekly_digest(bot: Bot, user_id: int):
    async with async_session() as session:
        entries = await get_last_week_entries(session, user_id)
        
        if len(entries) < 2:
            await bot.send_message(
                chat_id=user_id,
                text="На прошлой неделе было слишком мало записей для анализа. Жду твоих историй на этой неделе! 😉"
            )
            return
        
        digest = await generate_weekly_digest(entries)
        await bot.send_message(
            chat_id=user_id,
            text=digest
        )
    
def schedule_weekly_digest(bot: Bot, user_id: int):
    scheduler.add_job(
        func=run_weekly_digest,
        trigger='cron',
        day_of_week='mon',
        hour=10,
        minute=0,
        timezone='Europe/Moscow',
        id=f"digest_{user_id}",
        replace_existing=True,
        kwargs={
            'bot': bot,
            'user_id': user_id
        }
    )