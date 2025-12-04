from jose import jwt, JWTError
from datetime import datetime
import os

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
