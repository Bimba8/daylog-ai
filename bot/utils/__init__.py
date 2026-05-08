# utils package

# FIX: CQ-01 — Утилитарная функция валидации времени, чтобы не дублировать
# один и тот же try/except datetime.strptime в двух хендлерах (onboarding + settings).
from datetime import datetime


def validate_time(text: str) -> str | None:
    """Проверить, что строка имеет формат ЧЧ:ММ и является корректным временем.
    
    Возвращает нормализованную строку времени при успехе, None при ошибке.
    Нормализация: '9:05' → '09:05' (через strftime).
    """
    try:
        parsed = datetime.strptime(text.strip(), "%H:%M")
        return parsed.strftime("%H:%M")
    except ValueError:
        return None
