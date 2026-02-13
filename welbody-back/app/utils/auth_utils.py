"""
Simple token utilities using URL-safe base64 encoding.

This is intentionally minimal: it encodes `user_id:role` and decodes it.
Used for lightweight authentication in local testing. Replace with JWT
for production.
"""
import base64
from typing import Dict
from fastapi import HTTPException, status
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def encode_token(user_id: str, role: str) -> str:
    payload = f"{user_id}:{role}"
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_token(token: str) -> Dict[str, str]:
    try:
        payload = base64.urlsafe_b64decode(token.encode()).decode()
        user_id, role = payload.split(":", 1)
        return {"user_id": user_id, "role": role}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def hash_password(password: str) -> str:
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
