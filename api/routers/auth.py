from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from api.security import validate_init_data, create_jwt_token

router = APIRouter(prefix="/auth", tags=["Auth"])

class AuthRequest(BaseModel):
    initData: str
    
@router.post("")
async def auth_telegram(req: AuthRequest):
    user_data = validate_init_data(req.initData)
    if user_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid telegram token")
    
    telegram_id = user_data['id']
    token = create_jwt_token(telegram_id)
    return {"access_token": token, "token_type": "bearer"}
    