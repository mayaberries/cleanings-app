from fastapi import Depends, HTTPException, Path, status

from app.models.clinics.clinic import ClinicInDB
from app.models.clinics.clinic_api_key import ClinicAPIKeyInDB
from app.models.auth.user import UserInDB
from app.db.repositories.clinic_api_keys import ClinicAPIKeysRepository
from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.clinics import get_clinic_by_id_from_path, user_can_manage_clinic


def check_clinic_admin_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
) -> None:
    """
    Same permission shape as clinics.check_clinic_modification_permissions
    (now sharing user_can_manage_clinic so the is_superuser bypass only
    needed defining once). Kept as a separate dependency function --
    rather than importing that one directly -- because API-key management
    is a distinct permission surface from clinic profile edits, e.g. it's
    plausible clinic_aux staff get profile-edit rights later without ever
    getting key-management rights.

    The admin CLI's `sites generate` / `generate-all` commands rely on the
    is_superuser bypass here to read a clinic's public key without being
    that clinic's own admin.
    """
    if not user_can_manage_clinic(user=current_user, clinic_id=clinic.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the admin of this clinic (or a platform administrator) may manage its API keys.",
        )


async def get_clinic_api_key_by_id_from_path(
        key_id: str = Path(...),
        clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
        keys_repo: ClinicAPIKeysRepository = Depends(get_repository(ClinicAPIKeysRepository)),
) -> ClinicAPIKeyInDB:
    key = await keys_repo.get_key_by_id(id=key_id)

    if not key or key.clinic_id != clinic.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No API key found with that id for this clinic.",
        )

    return key
