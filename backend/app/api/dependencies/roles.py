from typing import Callable
from fastapi import Depends, HTTPException, status

from app.models.auth.user import UserInDB, UserRole
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


def require_superuser(
    current_user: UserInDB = Depends(get_current_active_user),
) -> UserInDB:
    """
    Platform-operator gate, distinct from the clinic-scoped `role` field.
    `is_superuser` has existed on the users table since the original
    schema but was never checked anywhere -- there was no cross-tenant
    surface that needed it until the admin CLI (backend/cli/) started
    needing to list/act across all clinics rather than just one.

    Deliberately NOT settable through any HTTP endpoint (UserCreate has no
    is_superuser field) -- the only way to grant it is
    scripts/promote_superuser.py, run directly against the DB by whoever
    already has that access. No self-service privilege escalation path.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires platform administrator access.",
        )
    return current_user
