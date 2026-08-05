from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED

from app.models.clinic import ClinicCreate, ClinicUpdate, ClinicInDB, ClinicPublic
from app.models.user import UserInDB
from app.db.repositories.clinics import ClinicsRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.clinics import get_clinic_by_id_from_path, check_clinic_modification_permissions

router = APIRouter()


@router.post("/", response_model=ClinicInDB, name="clinics:create-clinic", status_code=HTTP_201_CREATED)
async def create_clinic(
    new_clinic: ClinicCreate = Body(..., embed=False),
    current_user: UserInDB = Depends(get_current_active_user),
    clinics_repo: ClinicsRepository = Depends(get_repository(ClinicsRepository)),
) -> ClinicInDB:
    return await clinics_repo.create_clinic_for_admin(new_clinic=new_clinic, requesting_user=current_user)


@router.post("/{clinic_id}/staff/join", response_model=ClinicInDB, name="clinics:join-clinic-as-staff")
async def join_clinic_as_staff(
    clinic_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    clinics_repo: ClinicsRepository = Depends(get_repository(ClinicsRepository)),
) -> ClinicInDB:
    return await clinics_repo.join_clinic_as_staff(clinic_id=clinic_id, requesting_user=current_user)


@router.get("/{clinic_id}/", response_model=ClinicInDB, name="clinics:get-clinic-by-id")
async def get_clinic_by_id(clinic: ClinicInDB = Depends(get_clinic_by_id_from_path)) -> ClinicInDB:
    return clinic


@router.put(
    "/{clinic_id}/",
    response_model=ClinicInDB,
    name="clinics:update-clinic-by-id",
    dependencies=[Depends(check_clinic_modification_permissions)],
)
async def update_clinic_by_id(
    clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
    clinic_update: ClinicUpdate = Body(..., embed=False),
    clinics_repo: ClinicsRepository = Depends(get_repository(ClinicsRepository)),
) -> ClinicInDB:
    return await clinics_repo.update_clinic(clinic=clinic, clinic_update=clinic_update)