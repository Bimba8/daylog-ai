import asyncio
import sentry_sdk

from loguru import logger
from config import config
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from db.database import init_db, async_session, engine
from db.queries import get_all_users
from bot.services.ai import ai_router
from bot.handlers.history import router as history_router
from bot.handlers.start import router as start_router
from bot.handlers.diary import router as diary_router
from bot.handlers.stats import router as stats_router
from bot.handlers.info import router as info_router
from bot.handlers.common import router as common_router
from bot.services.scheduler import scheduler, schedule_daily_reminder, schedule_global_weekly_digest, set_bot
from bot.services.saver import cancel_background_tasks
from bot.middlewares.throttle import ThrottleMiddleware
from bot.middlewares.db import DbSessionMiddleware
from bot.logging_config import setup_logging

setup_logging()
logger = logger.bind(module="BOOT")

if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        integrations=[AsyncioIntegration()],
        traces_sample_rate=1.0,
        environment="production"
    )


async def on_startup(bot: Bot):
    """При старте бота — восстановить напоминания для всех юзеров из БД.
    Persistent jobs (daily, digest) уже хранятся в Redis, но мы перезаписываем их
    через replace_existing=True, чтобы подхватить изменения настроек юзеров.
    """
    await ai_router.start()
    logger.info("Загрузка напоминалок из БД")
    
    async with async_session() as session:
        users = await get_all_users(session)

        # В цикле заводим только индивидуальные ежедневные напоминалки
        for user in users:
            schedule_daily_reminder(
                bot=bot,
                user_id=user.telegram_id,
                time_str=user.reminder_time,
                tz_str=user.timezone
            )

    # А фабрику дайджестов просто один раз запускаем БЕЗ параметров и ВНЕ цикла
    schedule_global_weekly_digest()

    logger.info("Напоминалки загружены для {} юзеров", len(users))

async def on_shutdown(bot: Bot):
    logger.info("Остановка бота...")
    # Порядок остановки: сначала фоновые задачи, потом БД.
    # Иначе задачи получат OperationalError на закрытом engine.
    await ai_router.close()
    await cancel_background_tasks()
    scheduler.shutdown(wait=False)
    await engine.dispose()
    logger.info("Планировщик, фоновые задачи и БД закрыты")

async def main():
    await init_db()
    
    # Bot, storage, dispatcher создаются здесь (не на уровне модуля)
    # для корректного lifecycle и тестируемости.
    bot = Bot(
        token=config.BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = RedisStorage.from_url(config.REDIS_URL)
    dp = Dispatcher(storage=storage)
    
    # Middleware: throttle ПЕРВЫМ (до открытия DB-сессии)
    dp.update.middleware(ThrottleMiddleware())
    dp.update.middleware(DbSessionMiddleware())
    
    # Регистрация роутеров (порядок важен: common_router — catch-all, всегда последний)
    dp.include_router(start_router)
    dp.include_router(stats_router)
    dp.include_router(history_router)
    dp.include_router(info_router)
    dp.include_router(diary_router)
    dp.include_router(common_router)
    
    # Ссылка на bot устанавливается ДО scheduler.start(),
    # чтобы persistent jobs из Redis могли использовать get_bot().
    set_bot(bot)
    scheduler.start()
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("Бот запущен, ожидание сообщений")
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен оператором (KeyboardInterrupt)")