# utils package

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_DEFAULT_TZ = "Europe/Moscow"


def validate_time(text: str) -> str | None:
    """Валидация строки времени в формате ЧЧ:ММ. Нормализует '9:05' → '09:05'."""
    try:
        parsed = datetime.strptime(text.strip(), "%H:%M")
        return parsed.strftime("%H:%M")
    except ValueError:
        return None


def safe_tz(tz_str: str) -> ZoneInfo:
    """Безопасное создание ZoneInfo. При невалидной строке — fallback на Москву."""
    try:
        return ZoneInfo(tz_str)
    except (ZoneInfoNotFoundError, KeyError):
        return ZoneInfo(_DEFAULT_TZ)
