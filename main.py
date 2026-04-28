import asyncio

from config import config
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from db.database import init_db, async_session
from db.queries import get_all_users
from bot.handlers.history import router as history_router
from bot.handlers.start import router as start_router
from bot.handlers.diary import router as diary_router
from bot.handlers.stats import router as stats_router
from bot.services.scheduler import scheduler, schedule_daily_reminder

TOKEN = config.BOT_TOKEN

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(start_router)
dp.include_router(stats_router)
dp.include_router(history_router)
dp.include_router(diary_router)

async def on_startup(bot: Bot):
    print("🌅 Бот просыпается! Заряжаем ежедневные будильники...")
    
    async with async_session() as session:
        users = await get_all_users(session)
        
        for user in users:
            schedule_daily_reminder(
                bot=bot,
                user_id=user.telegram_id,
                time_str=user.reminder_time,
                tz_str=user.timezone
            )
    
    print(f"✅ Будильники заряжены для {len(users)} пользователей!")

async def main():
    await init_db()
    print("✅ Бот успешно запущен и ждет сообщений!")
    scheduler.start()
    dp.startup.register(on_startup)
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Давай братишка, отдыхаем")