from fastapi import Depends, HTTPException, Path, status

from app.models.clinics.clinic import ClinicInDB
from app.models.auth.user import UserInDB
from app.db.repositories.clinics import ClinicsRepository
from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user


async def get_clinic_by_id_from_path(
        clinic_id: str = Path(...),
        clinics_repo: ClinicsRepository = Depends(get_repository(ClinicsRepository)),
) -> ClinicInDB:
    clinic = await clinics_repo.get_clinic_by_id(id=clinic_id)
    if not clinic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No clinic found with that id.")
    return clinic


def user_can_manage_clinic(*, user: UserInDB, clinic_id: str) -> bool:
    """Single place both this file and clinic_api_keys.py defer to, so a
    platform operator (is_superuser) only had to be wired in once. A
    superuser can manage *any* clinic; a clinic_admin only their own."""
    if user.is_superuser:
        return True
    return user.role == "clinic_admin" and user.clinic_id == clinic_id


def check_clinic_modification_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
) -> None:
    if not user_can_manage_clinic(user=current_user, clinic_id=clinic.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the admin of this clinic (or a platform administrator) may modify it.",
        )
