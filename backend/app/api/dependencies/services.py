from fastapi import HTTPException, Depends, Path, status

from app.models.user import UserInDB
from app.models.service import ServiceInDB, ServicePublic

from app.db.repositories.services import ServicesRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user


async def get_service_by_id_from_path(
    service_id: str = Path(...),
    current_user: UserInDB = Depends(get_current_active_user),
    services_repo: ServicesRepository = Depends(
        get_repository(ServicesRepository)),
) -> ServicePublic:
    service = await services_repo.get_service_by_id(id=service_id, requesting_user=current_user)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No service found with that id."
        )
    return service


async def check_service_modification_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServicePublic = Depends(get_service_by_id_from_path),
) -> None:
    if not user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action forbidden. Users are only able to modify services they own"
        )


def user_owns_service(*, user: UserInDB, service: ServicePublic) -> bool:
    if isinstance(service.owner, str):
        return service.owner == user.id

    return service.owner.id == user.id
