from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, field_validator
import re
from api.deps import get_current_user, get_db
from db.models import User

# Whitelist допустимых IANA-таймзон (из bot/keyboards/main_kb.py)
_VALID_TIMEZONES = {
    "Europe/Kaliningrad", "Europe/Moscow", "Europe/Samara",
    "Asia/Yekaterinburg", "Asia/Omsk", "Asia/Krasnoyarsk",
    "Asia/Irkutsk", "Asia/Yakutsk", "Asia/Vladivostok",
    "Asia/Magadan", "Asia/Kamchatka",
    # UTC offsets for EN locale
    "Etc/GMT+12", "Etc/GMT+11", "Etc/GMT+10", "Etc/GMT+9", "Etc/GMT+8",
    "Etc/GMT+7", "Etc/GMT+6", "Etc/GMT+5", "Etc/GMT+4", "Etc/GMT+3",
    "Etc/GMT+2", "Etc/GMT+1", "UTC",
    "Etc/GMT-1", "Etc/GMT-2", "Etc/GMT-3", "Etc/GMT-4", "Etc/GMT-5",
    "Etc/GMT-6", "Etc/GMT-7", "Etc/GMT-8", "Etc/GMT-9", "Etc/GMT-10",
    "Etc/GMT-11", "Etc/GMT-12", "Etc/GMT-13", "Etc/GMT-14",
}

_TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("")
async def get_my_profile(user: User = Depends(get_current_user)):
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "created_at": user.created_at,
        "timezone": user.timezone,
        "reminder_time": user.reminder_time,
        "digest_day": user.digest_day,
        "digest_time": user.digest_time,
        "language_code": user.language_code
    }
    
class SettingsUpdate(BaseModel):
    timezone: str | None = None
    reminder_time: str | None = None
    digest_day: int | None = None
    digest_time: int | None = None
    language_code: str | None = None

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v):
        if v is not None and v not in _VALID_TIMEZONES:
            raise ValueError(f"Invalid timezone: {v}")
        return v
    
    @field_validator("reminder_time")
    @classmethod
    def validate_reminder_time(cls, v):
        if v is not None and not _TIME_PATTERN.match(v):
            raise ValueError("Time must be in HH:MM format (00:00–23:59)")
        return v
    
    @field_validator("digest_day")
    @classmethod
    def validate_digest_day(cls, v):
        if v is not None and not (0 <= v <= 6):
            raise ValueError("digest_day must be 0–6 (Mon–Sun)")
        return v
    
    @field_validator("digest_time")
    @classmethod
    def validate_digest_time(cls, v):
        if v is not None and not (0 <= v <= 23):
            raise ValueError("digest_time must be 0–23")
        return v
    
    
@router.post("/settings")
async def update_settings(
    settings: SettingsUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    if settings.timezone is not None:
        user.timezone = settings.timezone
    if settings.reminder_time is not None:
        user.reminder_time = settings.reminder_time
    if settings.digest_day is not None:
        user.digest_day = settings.digest_day
    if settings.digest_time is not None:
        user.digest_time = settings.digest_time
    if settings.language_code is not None and settings.language_code in ("ru", "en"):
        if user.language_code != settings.language_code:
            user.language_code = settings.language_code
            user.cached_insights = None
    
    await session.commit()
    return {"status": "success"}