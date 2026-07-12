import hashlib
import hmac
import json
import time
import jwt
from urllib.parse import parse_qsl
from datetime import datetime, timedelta, timezone
from config import config


BOT_TOKEN = config.BOT_TOKEN
JWT_SECRET = config.JWT_SECRET

# Максимально допустимый возраст auth_date (в секундах)
_INIT_DATA_MAX_AGE = 300  # 5 минут


def validate_init_data(init_data):
    data = dict(parse_qsl(init_data))
    data_hash = data.pop('hash', None)
    
    if not data_hash:
        return None
    
    # Проверяем auth_date — защита от replay-атак
    auth_date_str = data.get('auth_date')
    if not auth_date_str:
        return None
    
    try:
        auth_date = int(auth_date_str)
    except (ValueError, TypeError):
        return None
    
    if abs(time.time() - auth_date) > _INIT_DATA_MAX_AGE:
        return None
    
    data_check_string = "\n".join(sorted([f"{k}={v}" for k, v in data.items()]))
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest() 
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(data_hash, calculated_hash):
        return None
    
    user = data.get('user')
    if not user:
        return None
    return json.loads(user)

  
def create_jwt_token(user_id: int):
    payload = {
        'sub': str(user_id),
        'exp': datetime.now(timezone.utc) + timedelta(days=7)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload['sub']
        return int(user_id)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

