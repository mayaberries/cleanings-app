from fastapi import APIRouter, Body, Depends

from app.models.clinics.clinic import ClinicInDB
from app.models.clinics.clinic_availability import ClinicAvailabilityInDB, ClinicAvailabilityUpdate
from app.db.repositories.clinic_availability import ClinicAvailabilityRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.clinics import get_clinic_by_id_from_path, check_clinic_modification_permissions

router = APIRouter()


@router.get("/", response_model=ClinicAvailabilityInDB, name="clinic-availability:get-availability")
async def get_clinic_availability(
    clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
    availability_repo: ClinicAvailabilityRepository = Depends(get_repository(ClinicAvailabilityRepository)),
) -> ClinicAvailabilityInDB:
    return await availability_repo.get_or_create_availability(clinic_id=clinic.id)


@router.put(
    "/",
    response_model=ClinicAvailabilityInDB,
    name="clinic-availability:update-availability",
    dependencies=[Depends(check_clinic_modification_permissions)],
)
async def update_clinic_availability(
    clinic: ClinicInDB = Depends(get_clinic_by_id_from_path),
    availability_update: ClinicAvailabilityUpdate = Body(..., embed=False),
    availability_repo: ClinicAvailabilityRepository = Depends(get_repository(ClinicAvailabilityRepository)),
) -> ClinicAvailabilityInDB:
    return await availability_repo.update_availability(clinic_id=clinic.id, availability_update=availability_update)