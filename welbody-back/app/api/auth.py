from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.security import ROLE_PERMISSIONS, normalize_role
from app.core.dependencies import get_db
from app.models.user import User
from app.utils.auth_utils import encode_token, decode_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: Optional[str] = None
    username: str
    permissions: list[str] = Field(default_factory=list)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Sign in a user. Returns a simple bearer token that encodes user_id and role.

    This lightweight token is suitable for local testing. Include it as
    `Authorization: Bearer <token>` in subsequent requests.
    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.hashed_password or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = encode_token(user.user_id, user.role or "")
    normalized_role = normalize_role(user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.role,
        "username": user.username,
        "permissions": ROLE_PERMISSIONS.get(normalized_role, []),
    }


@router.get("/me")
def me(authorization: Optional[str] = Header(None)):
    """Return decoded token info for the current bearer token."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")
    token = authorization.split(" ", 1)[1]
    data = decode_token(token)
    return data
