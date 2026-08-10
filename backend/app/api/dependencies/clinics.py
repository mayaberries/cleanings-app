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


def check_clinic_modification_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
) -> None:
    if current_user.role != "clinic_admin" or current_user.clinic_id != clinic.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the admin of this clinic may modify it.",
        )