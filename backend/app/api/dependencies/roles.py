from typing import Callable, List
from fastapi import Depends, HTTPException, status

from app.models.user import UserInDB, UserRole
from app.api.dependencies.auth import get_current_active_user


def require_role(*allowed_roles: UserRole) -> Callable:
    def check_role(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )
        return current_user

    return check_role