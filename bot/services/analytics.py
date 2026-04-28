import json
from aiogram import Bot
from bot.services.ai import get_ai_metrics
from db.database import async_session
from db.queries import update_diary_metrics

async def generate_and_save_metrics(bot: Bot, chat_id: int, entry_id: int, user_text: str):
    response = await get_ai_metrics(user_text)
    
    if not response:
        print("⚠️ AI не смог составить валидный JSON")
        return
    else:
        metrics = json.dumps(response, ensure_ascii=False)
        
        async with async_session() as session:
            await update_diary_metrics(session=session, entry_id=entry_id, metrics_json=metrics)
    
    mood_score = response.get("mood", 0)
    energy_score = response.get("energy", 0)
    stress_score = response.get("stress", 0)
    productivity_score = response.get("productivity", 0)
    summary_text = response.get("summary", "Без комментариев.")
    
    try: 
        avg_score = (mood_score + energy_score + stress_score + productivity_score) / 4
        final_text = f"📊 Итоги дня: {avg_score} / 5\n\n📝 {summary_text}"
        await bot.send_message(chat_id=chat_id, text=final_text)
    
    except Exception as e:
        print(f"Не удалось вывести среднюю оценку метрик - {e}")