from typing import List

from fastapi import APIRouter, Body, status
from fastapi.param_functions import Depends

from app.api.dependencies.appointments import (
    check_appointment_confirmation_permissions,
    check_appointment_cancel_permissions,
    check_appointment_create_permissions,
    check_appointment_get_permissions,
    check_appointment_list_permissions,
    check_appointment_withdrawal_permissions,
    get_appointment_by_id_from_path,
)
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.services import get_service_by_id_from_path
from app.db.repositories.appointments import AppointmentsRepository
from app.models.appointment import AppointmentCreate, AppointmentInDB, AppointmentPublic, AppointmentRequestIn
from app.models.service import ServiceInDB
from app.models.user import UserInDB

router = APIRouter()


@router.post(
    "/", response_model=AppointmentPublic, name="appointments:create-appointment",
    status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_appointment_create_permissions)],
)
async def create_appointment(
        appointment_in: AppointmentRequestIn = Body(..., embed=False),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        current_user: UserInDB = Depends(get_current_active_user),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentPublic:
    created = await appointments_repo.create_appointment_for_service(
        new_appointment=AppointmentCreate(
            service_id=service.id,
            user_id=current_user.id,
            pet_id=appointment_in.pet_id,
            start_time=appointment_in.start_time,
        ),
        service=service,
    )
    return await appointments_repo.populate_appointment(appointment=created)


@router.get(
    "/", response_model=List[AppointmentPublic], name="appointments:list-appointments-for-service",
    status_code=status.HTTP_200_OK, dependencies=[Depends(check_appointment_list_permissions)],
)
async def list_appointments_for_service(
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> List[AppointmentPublic]:
    return await appointments_repo.list_appointments_for_service(service=service)


@router.get(
    "/{appointment_id}", response_model=AppointmentPublic, name="appointments:get-appointment-by-id",
    status_code=status.HTTP_200_OK, dependencies=[Depends(check_appointment_get_permissions)],
)
async def get_appointment_by_id(
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentPublic:
    return await appointments_repo.populate_appointment(appointment=appointment)


@router.put(
    "/{appointment_id}/confirm", response_model=AppointmentPublic, name="appointments:confirm-appointment",
    status_code=status.HTTP_200_OK, dependencies=[Depends(check_appointment_confirmation_permissions)],
)
async def confirm_appointment(
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentPublic:
    confirmed = await appointments_repo.confirm_appointment(appointment=appointment)
    return await appointments_repo.populate_appointment(appointment=confirmed)


@router.put(
    "/{appointment_id}/cancel", response_model=AppointmentPublic, name="appointments:cancel-appointment",
    status_code=status.HTTP_200_OK, dependencies=[Depends(check_appointment_cancel_permissions)],
)
async def cancel_appointment(
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentPublic:
    cancelled = await appointments_repo.cancel_appointment(appointment=appointment)
    return await appointments_repo.populate_appointment(appointment=cancelled)


@router.delete(
    "/{appointment_id}", response_model=AppointmentPublic, name="appointments:withdraw-appointment",
    status_code=status.HTTP_200_OK, dependencies=[Depends(check_appointment_withdrawal_permissions)],
)
async def withdraw_appointment(
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentPublic:
    withdrawn = await appointments_repo.withdraw_appointment(appointment=appointment)
    return AppointmentPublic(**withdrawn.model_dump())
