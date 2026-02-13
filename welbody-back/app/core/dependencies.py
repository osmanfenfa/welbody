from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.security import normalize_role
from app.db.session import get_db
from app.utils.auth_utils import decode_token


def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        payload = decode_token(token)
        payload["role"] = normalize_role(payload.get("role"))
        return payload

    if x_user_id and x_user_role:
        return {"user_id": x_user_id, "role": normalize_role(x_user_role)}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication headers",
    )


def require_roles(*roles: str):
    allowed_roles = {normalize_role(role) for role in roles}

    def _role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        current_role = normalize_role(current_user.get("role"))
        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _role_checker


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    current_role = normalize_role(current_user.get("role"))
    if current_role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN users can perform this action",
        )
    return current_user
