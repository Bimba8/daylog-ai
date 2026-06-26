from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from api.deps import get_current_user, get_db
from db.models import User

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
        "digest_time": user.digest_time
    }
    
class SettingsUpdate(BaseModel):
    timezone: str | None = None
    reminder_time: str | None = None
    digest_day: int | None = None
    digest_time: int | None = None
    
    
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
    
    await session.commit()
    return {"status": "success"}