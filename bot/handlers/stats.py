import json
from loguru import logger
from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_user_entries, get_entry_count, get_or_create_user
from bot.keyboards.main_kb import get_report_kb
from datetime import datetime, timedelta

logger = logger.bind(module="HANDLER")

router = Router()

def calculate_stats(entries: list, total_count: int, tz_str: str = "UTC") -> dict | None:
    """FIX: BL-05 — Streak считается в таймзоне юзера, а не сервера.
    
    Проблема: datetime.now().date() возвращало серверную дату, а entry.created_at.date()
    — UTC-дату. Для юзера в UTC+5 запись в 23:00 локального (18:00 UTC) имела бы
    UTC-дату «сегодня», но если юзер проверяет статистику в 01:00 следующего дня по серверу,
    streak сломается.
    
    Решение: конвертируем и «сейчас», и created_at записей в таймзону юзера.
    """
    if not entries:
        return None
    
    # Расчет средних за последние записи (уже ограничены 7 штуками из БД)
    sums = {"mood": 0, "energy": 0, "stress": 0, "productivity": 0}
    count_with_metrics = 0
    
    for entry in entries:
        if entry.ai_metrics:
            try:
                data = json.loads(entry.ai_metrics)
                for metric in sums:
                    sums[metric] += data.get(metric, 0)
                count_with_metrics += 1
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Ошибка парсинга метрик записи {}: {}", entry.id, e)
    
    if count_with_metrics > 0:    
        for metric in sums:
            sums[metric] = round(sums[metric] / count_with_metrics, 1)
    
    # FIX: BL-05 — Стрик: конвертируем все даты в таймзону юзера перед сравнением.
    # created_at хранится в БД как naive UTC — добавляем tzinfo=UTC,
    # затем переводим в локальное время юзера и берём .date().
    from zoneinfo import ZoneInfo
    user_tz = ZoneInfo(tz_str)
    utc_tz = ZoneInfo("UTC")
    
    streak = 0
    target_date = datetime.now(user_tz).date()
    
    for entry in entries:
        # created_at — naive datetime в UTC, приводим к aware и конвертируем
        entry_date = entry.created_at.replace(tzinfo=utc_tz).astimezone(user_tz).date()
        
        if entry_date == target_date:
            streak += 1
            target_date -= timedelta(days=1)
        elif entry_date == target_date - timedelta(days=1) and streak == 0:
            # Если юзер ещё не писал сегодня, но вчерашняя запись есть — стрик от неё
            streak = 1
            target_date = entry_date - timedelta(days=1)
        elif entry_date < target_date:
            break
    
    return {
        "total_count": total_count,
        "streak": streak,
        "averages": sums
    }
    
@router.message(Command("stats"))
@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message, session: AsyncSession):
    # FIX: BL-05 — Загружаем юзера для его таймзоны (нужна для корректного стрика)
    user, _ = await get_or_create_user(session, message.from_user.id)
    
    # Загружаем только последние 7 записей (для средних и стрика) + общий count
    entries = await get_user_entries(session, message.from_user.id, order="desc", limit=7)
    total_count = await get_entry_count(session, message.from_user.id)
    
    if not entries:
        await message.answer(
            text=(
                "📊 <b>Статистика пока пуста</b>\n\n"
                "Напиши первый отчет, чтобы ИИ начал собирать твои метрики."
            ),
            reply_markup=get_report_kb()
        )
        return
    
    stats = calculate_stats(entries, total_count, tz_str=user.timezone)
    avg = stats['averages']
    
    response_text = (
        "📊 <b>Твоя статистика</b>\n\n"
        f"🏆 Всего записей: <b>{stats['total_count']}</b>\n"
        f"🔥 Текущий стрик: <b>{stats['streak']} дн.</b>\n\n"
        "📈 <b>Среднее за неделю:</b>\n"
        f"😌 Настроение: <b>{avg['mood']}</b>\n"
        f"⚡️ Энергия: <b>{avg['energy']}</b>\n"
        f"🧠 Продуктивность: <b>{avg['productivity']}</b>\n"
        f"🌪 Стресс: <b>{avg['stress']}</b>"
    )

    await message.answer(response_text)