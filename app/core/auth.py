from typing import List, Optional, Union
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.models.user import User, UserRole
from ..core.security import decode_access_token


class CurrentUser:
    def __init__(self, user: User):
        self.user = user


def get_current_user(Authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> CurrentUser:
    if not Authorization or not Authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = Authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.get(User, int(sub))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return CurrentUser(user)


def require_roles(allowed: List[Union[UserRole, str]]):
    # Normalize allowed to enum values
    normalized = {a if isinstance(a, str) else a.value for a in allowed}

    def _require(user_ctx: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        user_role_value = user_ctx.user.role.value if isinstance(user_ctx.user.role, UserRole) else str(user_ctx.user.role)
        if user_role_value not in normalized:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user_ctx

    return _require