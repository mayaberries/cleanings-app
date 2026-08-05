from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from starlette.status import HTTP_201_CREATED, HTTP_404_NOT_FOUND

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.services import get_service_by_id_from_path, check_service_modification_permissions
from app.db.repositories.services import ServicesRepository
from app.models.service import ServiceCreate, ServiceInDB, ServicePublic, ServiceUpdate
from app.models.user import UserInDB

router = APIRouter()


@router.get("/{service_id}/", response_model=ServicePublic, name="services:get-service-by-id")
async def get_service_by_id(
        service_id: str = Path(...),
        current_user: UserInDB = Depends(get_current_active_user),
        services_repo: ServicesRepository = Depends(
            get_repository(ServicesRepository))
) -> ServicePublic:
    service = await services_repo.get_service_by_id(id=service_id, requesting_user=current_user)

    if not service:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail="No service found with that id.")
    return service


@router.post("/", response_model=ServicePublic, name="services:create-service", status_code=HTTP_201_CREATED)
async def create_new_service(
        new_service: ServiceCreate = Body(..., embed=False),
        current_user: UserInDB = Depends(get_current_active_user),
        services_repo: ServicesRepository = Depends(
            get_repository(ServicesRepository)),
) -> ServicePublic:
    created_service = await services_repo.create_service(
        new_service=new_service,
        requesting_user=current_user
    )
    return created_service


@router.get("/", response_model=List[ServicePublic], name="services:list-all-user-services")
async def get_all_services(
        current_user: UserInDB = Depends(get_current_active_user),
        services_repo: ServicesRepository = Depends(get_repository(ServicesRepository))
) -> List[ServicePublic]:
    return await services_repo.list_all_clinic_services(
        requesting_user=current_user
    )


@router.put(
    "/{service_id}/",
    response_model=ServicePublic,
    name="services:update-service-by-id",
    dependencies=[Depends(check_service_modification_permissions)],
)
async def update_service_by_id(
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        service_update: ServiceUpdate = Body(..., embed=False),
        services_repo: ServicesRepository = Depends(
            get_repository(ServicesRepository)),
) -> ServicePublic:
    updated_service = await services_repo.update_service(
        service=service, service_update=service_update
    )

    if not updated_service:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No service found with that id.",
        )
    return updated_service


@router.delete(
    "/{service_id}/",
    response_model=str,
    name="services:delete-service-by-id",
    dependencies=[Depends(check_service_modification_permissions)]
)
async def delete_service_by_id(
        service_id: str = Path(..., title="The ID of the service to delete."),
        current_user: UserInDB = Depends(get_current_active_user),
        services_repo: ServicesRepository = Depends(
            get_repository(ServicesRepository)),
) -> str:
    return await services_repo.delete_service_by_id(id=service_id, requesting_user=current_user)
