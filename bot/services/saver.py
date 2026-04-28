import asyncio
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from db.database import async_session
from db.queries import add_diary_entry
from bot.services.analytics import generate_and_save_metrics

async def finalize_diary_entry(bot: Bot, chat_id: int, user_id: int, text: str, state: FSMContext = None):
    # 1. Сохраняем всё в базу и получаем ID записи для ИИ
    async with async_session() as session:
        new_entry = await add_diary_entry(session, user_id, text)
    
    # 2. Чистим стейт FSM, если он передан (для живых диалогов)
    if state:
        await state.clear()
        
    # 3. Самое главное: запускаем ИИ-анализ в фоне
    asyncio.create_task(generate_and_save_metrics(bot, chat_id, new_entry.id, text))
    
    return new_entry