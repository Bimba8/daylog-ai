import json
from loguru import logger
from aiogram import Bot
from bot.services.ai import get_ai_metrics
from bot.utils.telegram import safe_send
from bot.keyboards.main_kb import get_main_kb
from bot.lexicon.i18n import t
from db.database import async_session
from db.queries import update_diary_metrics

logger = logger.bind(module="AI")

async def generate_and_save_metrics(bot: Bot, chat_id: int, entry_id: int, user_text: str, loading_msg_id: int | None = None, lang: str = "ru"):
    response = await get_ai_metrics(user_text, lang=lang)
    
    if not response:
        logger.warning("ИИ не вернул валидные метрики")
        return

    metrics = json.dumps(response, ensure_ascii=False)
    
    """Фоновая генерация и сохранение AI-метрик."""
    # Фоновая задача — middleware-сессия недоступна, используем standalone.
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
        is_chill = (productivity_score > 3 and energy_score < 3) or (mood_score >= 4 and stress_score <= 2 and energy_score < 3)
        
        if is_chill:
            avg_score = round((mood_score + adjusted_stress) / 2, 1)
        else:
            avg_score = round((mood_score + energy_score + adjusted_stress + productivity_score) / 4, 1)
        
        
        final_text = t('analytics_day_summary', lang).format(score=avg_score, summary=summary_text)
        
        # safe_send обрабатывает TelegramForbiddenError и rate limits
        # Если у нас есть ID заглушки, просто меняем её текст на итоги дня
        # 1. Сначала молча убиваем заглушку (так как на ней нет меню, интерфейс не дернется)
        if loading_msg_id:
            try:
                await bot.delete_message(chat_id, loading_msg_id)
            except Exception:
                pass
                
        # 2. Отправляем финальные итоги и жестко привязываем к ним клавиатуру
        await bot.send_message(
            chat_id=chat_id, 
            text=final_text, 
            reply_markup=get_main_kb()
        )
    
    except Exception as e:
        logger.error("Ошибка расчёта/отправки средних метрик: {}", e)