from fastapi import Depends, HTTPException, Path, status

from app.models.auth.user import UserInDB, UserRole
from app.models.clinics.clinic_owner_profile import ClinicOwnerProfileInDB

from app.db.repositories.clinic_owner_profiles import ClinicOwnerProfilesRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.roles import require_role


async def get_current_clinic_staff(
    current_user: UserInDB = Depends(require_role(UserRole.clinic_admin, UserRole.clinic_aux)),
) -> UserInDB:
    """Staff role alone isn't enough — they also need to actually belong to
    a clinic (edge case: a clinic_admin/aux account exists but hasn't been
    attached to one yet, or was detached)."""
    if not current_user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a clinic to manage owner records.",
        )
    return current_user


async def get_clinic_owner_pivot_by_id_from_path(
    owner_profile_id: str = Path(...),
    current_user: UserInDB = Depends(get_current_clinic_staff),
    pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
) -> ClinicOwnerProfileInDB:
    """The whole point: the path only ever takes an owner_profile_id — the
    clinic is never a client-supplied value, it comes from current_user.
    A pivot from another clinic simply doesn't exist from this caller's
    point of view — 404, not 403, so we don't even confirm the owner
    exists on the platform at all to a clinic that has no relationship
    with them."""
    pivot = await pivots_repo.get_pivot_for_clinic_and_owner(
        clinic_id=current_user.clinic_id, owner_profile_id=owner_profile_id
    )

    if not pivot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No owner found with that id at your clinic.",
        )

    return pivot