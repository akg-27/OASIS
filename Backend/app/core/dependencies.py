# app/core/dependencies.py
from fastapi import Depends, Header
from app.utils.auth_utils import decode_token

async def get_current_user(Authorization: str = Header(None)):
    if not Authorization:
        return None

    token = Authorization.replace("Bearer ", "")
    user = decode_token(token)
    return user

# role based guard
def role_required(roles: list):
    async def guard(user=Depends(get_current_user)):
        if not user or user.get("role") not in roles:
            return {"status": "error", "detail": "Access denied"}
        return user
    return guard
