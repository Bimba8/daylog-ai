import json
from loguru import logger
from aiogram import Bot
from bot.services.ai import get_ai_metrics
from bot.utils.telegram import safe_send  # FIX: CRIT-05
from db.database import async_session
from db.queries import update_diary_metrics

logger = logger.bind(module="AI")

async def generate_and_save_metrics(bot: Bot, chat_id: int, entry_id: int, user_text: str):
    response = await get_ai_metrics(user_text)
    
    if not response:
        logger.warning("ИИ не вернул валидные метрики")
        return

    metrics = json.dumps(response, ensure_ascii=False)
    
    # FIX: CRIT-04 — Эта функция работает в фоновой asyncio.Task (запущена из saver.py),
    # поэтому middleware-сессия хендлера сюда не доходит. Открываем собственную сессию
    # с явным commit при успехе и rollback при ошибке, чтобы не потерять метрики
    # и не оставить соединение в «грязном» состоянии.
    async with async_session() as session:
        try:
            await update_diary_metrics(session=session, entry_id=entry_id, metrics_json=metrics)
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Не удалось сохранить метрики для записи {}: {}", entry_id, e)
            return
    
    mood_score = response.get("mood", 0)
    energy_score = response.get("energy", 0)
    stress_score = response.get("stress", 0)
    productivity_score = response.get("productivity", 0)
    summary_text = response.get("summary", "Без комментариев.")
    
    try: 
        # Стресс — инвертированная метрика (5 = плохо), поэтому переворачиваем его для корректного среднего
        adjusted_stress = 6 - stress_score
        avg_score = round((mood_score + energy_score + adjusted_stress + productivity_score) / 4, 1)
        final_text = f"📊 Итоги дня: {avg_score} / 5\n\n📝 {summary_text}"
        # FIX: CRIT-05 — safe_send вместо голого bot.send_message
        await safe_send(bot, chat_id, text=final_text)
    
    except Exception as e:
        logger.error("Ошибка расчёта/отправки средних метрик: {}", e)