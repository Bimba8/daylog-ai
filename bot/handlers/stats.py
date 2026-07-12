import json
from loguru import logger
from aiogram import Router, F, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from db.queries import get_user_entries, get_entry_count, get_or_create_user
from bot.keyboards.main_kb import get_report_kb
from bot.utils import safe_tz
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from bot.lexicon.i18n import t, all_values

logger = logger.bind(module="HANDLER")

router = Router()

def calculate_stats(metric_entries: list, streak_entries: list, total_count: int, tz_str: str = "UTC") -> dict | None:
    """Расчёт статистики: средние метрики (по metric_entries) и стрик (по streak_entries).
    
    Стрик считается в таймзоне юзера, а не сервера.
    """
    if not metric_entries:
        return None
    
    # Средние за последние записи (ограничены 7 штуками)
    sums = {"mood": 0, "energy": 0, "stress": 0, "productivity": 0}
    count_with_metrics = 0
    
    for entry in metric_entries:
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
    
    # Стрик: конвертируем все даты в таймзону юзера перед сравнением.
    # created_at хранится как naive UTC — добавляем tzinfo=UTC, переводим в локальное.
    user_tz = safe_tz(tz_str)
    utc_tz = ZoneInfo("UTC")
    
    streak = 0
    target_date = datetime.now(user_tz).date()
    
    for entry in streak_entries:
        entry_date = entry.created_at.replace(tzinfo=utc_tz).astimezone(user_tz).date()
        
        if entry_date == target_date:
            streak += 1
            target_date -= timedelta(days=1)
        elif entry_date == target_date - timedelta(days=1) and streak == 0:
            # Юзер ещё не писал сегодня, но вчерашняя запись есть — стрик от неё
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
@router.message(F.text.in_(all_values('kb_stats')))
async def show_stats(message: types.Message, session: AsyncSession, lang: str = "ru"):
    """Показать статистику юзера: средние метрики и стрик."""
    user, _ = await get_or_create_user(session, message.from_user.id)
    
    # Последние 7 записей для средних метрик
    metric_entries = await get_user_entries(session, message.from_user.id, order="desc", limit=7)
    # До 365 записей для стрика (без лимита — не нужно загружать все 1000+)
    streak_entries = await get_user_entries(session, message.from_user.id, order="desc", limit=365)
    total_count = await get_entry_count(session, message.from_user.id)
    
    if not metric_entries:
        await message.answer(
            text=t('stats_empty', lang),
            reply_markup=get_report_kb(lang)
        )
        return
    
    stats = calculate_stats(metric_entries, streak_entries, total_count, tz_str=user.timezone)
    avg = stats['averages']
    
    response_text = t('stats_report', lang).format(
        total_count=stats['total_count'],
        streak=stats['streak'],
        mood=avg['mood'],
        energy=avg['energy'],
        productivity=avg['productivity'],
        stress=avg['stress']
    )

    await message.answer(response_text)