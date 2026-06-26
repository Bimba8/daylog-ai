import hashlib
import hmac
import json
import jwt
from urllib.parse import parse_qsl
from datetime import datetime, timedelta
from config import config


BOT_TOKEN = config.BOT_TOKEN


def validate_init_data(init_data):
    data = dict(parse_qsl(init_data))
    data_hash = data.pop('hash', None)
    data_check_string = "\n".join(sorted([f"{k}={v}" for k, v in data.items()]))
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest() 
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    if data_hash != calculated_hash:
        return None
    else:
        user = data['user']
        return json.loads(user)

  
def create_jwt_token(user_id: int):
    payload = {
        'sub': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, BOT_TOKEN, algorithm="HS256")
    return token


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, BOT_TOKEN, algorithms=["HS256"])
        user_id = payload['sub']
        return int(user_id)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
