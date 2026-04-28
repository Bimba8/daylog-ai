import json
from aiogram import Router, F, types
from db.database import async_session
from db.queries import get_all_user_entries
from datetime import datetime, timedelta

router = Router()

def calculate_stats(entries):
    if not entries:
        return None
    
    total_count = len(entries)
    
    # Расчет средних за 7 дней
    last_week = entries[:7]
    sums = {"mood": 0, "energy": 0, "stress": 0, "productivity": 0}
    count_with_metrics = 0
    
    for entry in last_week:
        if entry.ai_metrics:
            data = json.loads(entry.ai_metrics)
            try:
                for metric in sums:
                    sums[metric] += data.get(metric, 0)
                    
                count_with_metrics += 1
            except Exception as e:
                print(f"Ошибка парсинга JSON: {e}")
    
    if count_with_metrics > 0:    
        for metric in sums:
            sums[metric] = round(sums[metric] / count_with_metrics, 1)
    
    streak = 0
    target_date = datetime.now().date()
    
    for entry in entries:
        entry_date = entry.created_at.date()
        
        if entry_date == target_date:
            streak += 1
            target_date -= timedelta(days=1)
        elif entry_date == target_date - timedelta(days=1) and streak == 0:
            # Если это самая первая проверка и мы нашли вчерашнюю запись вместо сегодняшней
            streak = 1
            target_date = entry_date - timedelta(days=1)
        elif entry_date < target_date:
            break
    
    return {
        "total_count": total_count,
        "streak": streak,
        "averages": sums # твой результат средних
    }
    
@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    async with async_session() as session:
        entries = await get_all_user_entries(session, message.from_user.id)
        
        if not entries:
            await message.answer("У тебя пока нет записей для статистики. Начни вести дневник! 😉")
            return
        
        stats = calculate_stats(entries)
        
        # Подсказка: averages — это твой словарь sums из функции
        avg = stats['averages']
        
        response_text = (
            f"📊 <b>Твоя статистика</b>\n\n"
            f"🏆 Всего записей: <b>{stats['total_count']}</b>\n"
            f"🔥 Текущий стрик: <b>{stats['streak']} дн.</b>\n\n"
            f"📈 <b>Среднее за неделю:</b>\n"
            f"😌 Настроение: <b>{avg['mood']}</b>\n"
            f"⚡️ Энергия: <b>{avg['energy']}</b>\n"
            f"🧠 Продуктивность: <b>{avg['productivity']}</b>\n"
            f"🌪 Стресс: <b>{avg['stress']}</b>"
        )

        await message.answer(response_text)