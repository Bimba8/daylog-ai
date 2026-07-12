from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from api.security import validate_init_data, create_jwt_token
from api.deps import get_db
from db.queries import get_user

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    initData: str
    
@router.post("")
async def auth_telegram(req: AuthRequest, session: AsyncSession = Depends(get_db)):
    user_data = validate_init_data(req.initData)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid telegram token")
    
    telegram_id = user_data['id']
    
    user = await get_user(session, telegram_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not found in database. Start the bot first.")
        
    token = create_jwt_token(telegram_id)
    return {"access_token": token, "token_type": "bearer"}
    