from fastapi import HTTPException, Depends, Path, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.services import ServicesRepository
from app.models.services.service import ServicePublic
from app.models.auth.user import UserInDB


async def get_service_by_id_from_path(
        service_id: str = Path(...),
        current_user: UserInDB = Depends(get_current_active_user),
        services_repo: ServicesRepository = Depends(get_repository(ServicesRepository)),
) -> ServicePublic:
    service = await services_repo.get_service_by_id(id=service_id, requesting_user=current_user)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No service found with that id."
        )
    return service


def get_service_clinic_id(service: ServicePublic) -> str:
    return service.clinic if isinstance(service.clinic, str) else service.clinic.id


async def check_service_modification_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServicePublic = Depends(get_service_by_id_from_path),
) -> None:
    if not user_can_manage_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are only able to modify services belonging to their own clinic."
        )


def user_can_manage_service(*, user: UserInDB, service: ServicePublic) -> bool:
    """Any staff member (admin or aux) of the clinic that owns this service can manage it."""
    if not user.clinic_id:
        return False
    return user.clinic_id == get_service_clinic_id(service)
