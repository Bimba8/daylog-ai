import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.deps import get_db, get_current_user
from bot.handlers.stats import calculate_stats
from bot.utils import safe_tz
from bot.services.ai import generate_user_insights
from db.models import User
from db.queries import get_entry_count, get_user_entries, get_user_digest, get_entries_by_date_range, get_latest_diary_entry

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/metrics")
async def get_metrics(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    total = await get_entry_count(session, user.telegram_id)
    entries = await get_user_entries(session, user.telegram_id, order="desc", limit=105)
    metric_entries = entries[:7]
    stats = calculate_stats(metric_entries, entries, total, tz_str=user.timezone)
    
    if not stats:
        return {
            "total_entries": 0,
            "streak": 0,
            "avg_mood": 0,
            "activity_percent": 0,
            "heatmap": [False for _ in range(105)]
        }
    
    user_tz = safe_tz(user.timezone)
    today = datetime.now(user_tz).date()
    utc_tz = ZoneInfo("UTC")
    entry_dates = {e.created_at.replace(tzinfo=utc_tz).astimezone(user_tz).date() for e in entries}
    
    # Расчет дельты настроения (последние 7 дней vs предыдущие 7 дней)
    current_moods, prev_moods = [], []
    
    for e in entries:
        e_date = e.created_at.replace(tzinfo=utc_tz).astimezone(user_tz).date()
        
        if (today - timedelta(days=6)) <= e_date <= today:
            if e.ai_metrics:
                try:
                    data = json.loads(e.ai_metrics)
                    if "mood" in data:
                        current_moods.append(data["mood"])
                except (json.JSONDecodeError, TypeError):
                    pass
                
        elif (today - timedelta(days=13)) <= e_date <= (today - timedelta(days=7)):
            if e.ai_metrics:
                try:
                    data = json.loads(e.ai_metrics)
                    if "mood" in data:
                        prev_moods.append(data["mood"])
                except (json.JSONDecodeError, TypeError):
                    pass
                
    avg_current = round(sum(current_moods) / len(current_moods), 1) if current_moods else 0
    avg_prev = round(sum(prev_moods) / len(prev_moods), 1) if prev_moods else 0
    mood_delta = round(avg_current - avg_prev, 1) if (current_moods and prev_moods) else 0.0
    
    heatmap = [(today - timedelta(days=i)) in entry_dates for i in range(104, -1, -1)]
        
    active_days = sum(1 for i in range(30) if (today - timedelta(days=i)) in entry_dates)
    activity_percent = round((active_days / 30) * 100)
    
    return {
        "total_entries": total,
        "streak": stats["streak"],
        "avg_mood": stats["averages"]["mood"],
        "mood_delta": mood_delta,
        "activity_percent": activity_percent,
        "heatmap": heatmap
    }
    

@router.get("/calendar")
async def get_entries(
    limit: int = 30,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    entries = await get_user_entries(session, user.telegram_id, limit)
    digests = await get_user_digest(session, user.telegram_id, limit=5)
    
    formatted_items = []
    
    for entry in entries:
        formatted_items.append({
            "id": entry.id,
            "created_at": entry.created_at,
            "conversation_log": entry.conversation_log,
            "metrics": entry.ai_metrics,
            "type": "log"
        })
        
    for digest in digests:
        formatted_items.append({
            "id": digest.id,
            "created_at": digest.created_at,
            "content": digest.content,
            "type": "digest"
        })
        
    return {"items": formatted_items}


@router.get("/analytics")
async def get_analytics(
    period: str = "30days",
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    days = 7 if period == "7days" else 30
    user_tz = safe_tz(user.timezone)
    
    total_entries = await get_entry_count(session, user.telegram_id)
    
    # Высчитываем локальные границы дат
    now_local = datetime.now(user_tz)
    today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start_local = today_local - timedelta(days=days - 1)
    end_local = today_local + timedelta(days=1)
    
    # Переводим в UTC для точного запроса в базу
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    
    # Достаем реальные записи из БД
    entries = await get_entries_by_date_range(session, user.telegram_id, start_utc, end_utc)
    
    # Группируем метрики по локальной дате (YYYY-MM-DD)
    metrics_by_date = {}
    for entry in entries:
        entry_local_date = entry.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz).date()
        date_str = entry_local_date.isoformat()
        
        if entry.ai_metrics:
            try:
                parsed = json.loads(entry.ai_metrics)
                if date_str not in metrics_by_date:
                    metrics_by_date[date_str] = []
                metrics_by_date[date_str].append(parsed)
            except json.JSONDecodeError:
                pass
            
    # Формируем данные графика и интерполируем пустые дни
    chart_data = []
    total_mood = total_energy = total_stress = total_prod = 0
    days_with_data = 0
    last_known = {"mood": 0, "energy": 0, "stress": 0, "productivity": 0}
    
    ru_months = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]        # потом надо будет засунуть в лексикон файл нврн перед тем как делать англ локализацию
    ru_weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    
    for i in range(days):
        current_date = (start_local + timedelta(days=i)).date()
        date_str = current_date.isoformat()
        
        if days == 7:
            day_label = ru_weekdays[current_date.weekday()]
        else:
            day_label = f"{current_date.day} {ru_months[current_date.month - 1]}"
            
        daily_metrics = {"mood": 0, "energy": 0, "stress": 0, "productivity": 0}
        
        if date_str in metrics_by_date and metrics_by_date[date_str]:
            # Усредняем, если за день было несколько записей
            day_list = metrics_by_date[date_str]
            count = len(day_list)
            daily_metrics["mood"] = round(sum(m.get("mood", 0) for m in day_list) / count, 1)
            daily_metrics["energy"] = round(sum(m.get("energy", 0) for m in day_list) / count, 1)
            daily_metrics["stress"] = round(sum(m.get("stress", 0) for m in day_list) / count, 1)
            daily_metrics["productivity"] = round(sum(m.get("productivity", 0) for m in day_list) / count, 1)
            
            last_known = daily_metrics.copy()
            total_mood += daily_metrics["mood"]
            total_energy += daily_metrics["energy"]
            total_stress += daily_metrics["stress"]
            total_prod += daily_metrics["productivity"]
            days_with_data += 1
            
        else:
            # Если день пустой — берем значения предыдущего (линейная интерполяция)
            daily_metrics = last_known.copy()
            
        chart_data.append({
            "day": day_label,
            "mood": daily_metrics["mood"],
            "energy": daily_metrics["energy"],
            "stress": daily_metrics["stress"],
            "productivity": daily_metrics["productivity"]
        })
        
    # Считаем глобальное среднее (diff заглушаем нулями)
    global_avg = {
        "mood": {"value": round(total_mood / days_with_data, 1) if days_with_data else 0, "diff": "0.0"},
        "energy": {"value": round(total_energy / days_with_data, 1) if days_with_data else 0, "diff": "0.0"},
        "stress": {"value": round(total_stress / days_with_data, 1) if days_with_data else 0, "diff": "0.0"},
        "productivity": {"value": round(total_prod / days_with_data, 1) if days_with_data else 0, "diff": "0.0"},
    }
    
    insights_data = {
        "resources": ["Спорт", "Код", "Сон", "Прогулка"],
        "energy_leaks": ["Дедлайны", "Недосып", "Алкоголь"]
    }
    
    if user.cached_insights:
        try:
            insights_data = json.loads(user.cached_insights)
            
        except (json.JSONDecodeError, TypeError):
            pass
        
    latest_entry = await get_latest_diary_entry(session, user.telegram_id)
    
    if latest_entry:
        need_update = False
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        
        if not user.cached_insights or not user.insights_updated_at:
            need_update = True
        else:
            cache_age = now_utc - user.insights_updated_at
            
            if cache_age > timedelta(hours=24) and latest_entry.created_at >= user.insights_updated_at:
                need_update = True
                
        if need_update:
            recent = await get_user_entries(session, user.telegram_id, order="desc", limit=30)
            new_insight = await generate_user_insights(recent)
            
            if new_insight:
                insights_data = new_insight
                user.cached_insights = json.dumps(new_insight, ensure_ascii=False)
                user.insights_updated_at = now_utc
                await session.commit()
    
    return {
        "averages": global_avg,
        "chart": chart_data,
        "insights": insights_data,
        "total_entries": total_entries
    }