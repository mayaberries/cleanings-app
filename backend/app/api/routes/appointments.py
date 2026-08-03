from typing import List
from fastapi import APIRouter, status
from fastapi.param_functions import Depends

from app.models.appointment import AppointmentCreate, AppointmentInDB, AppointmentPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

from app.api.dependencies.services import get_service_by_id_from_path
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.appointments import (
    check_appointment_confirmation_permissions,
    check_appointment_cancel_permissions,
    check_appointment_create_permissions,
    check_appointment_get_permissions,
    check_appointment_list_permissions,
    get_appointment_for_service_from_current_user,
    get_appointment_for_service_from_user_by_path,
    list_appointments_for_service_by_id_from_path,
    check_appointment_withdrawal_permissions,
)

from app.db.repositories.appointments import AppointmentsRepository


router = APIRouter()


@router.post(
    "/",
    response_model=AppointmentPublic,
    name="appointments:create-appointment",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_appointment_create_permissions)]
)
async def create_appointment(
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    current_user: UserInDB = Depends(get_current_active_user),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository))
) -> AppointmentPublic:
    return await appointments_repo.create_appointment_for_service(
        new_appointment=AppointmentCreate(service_id=service.id, user_id=current_user.id)
    )


@router.get(
    "/",
    response_model=List[AppointmentPublic],
    name="appointments:list-appointments-for-service",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_appointment_list_permissions)]
)
async def list_appointments_for_service(
    appointments: List[AppointmentInDB] = Depends(list_appointments_for_service_by_id_from_path)
) -> List[AppointmentPublic]:
    return appointments


@router.get(
    "/{username}",
    response_model=AppointmentPublic,
    name="appointments:get-appointment-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_appointment_get_permissions)]
)
async def get_appointment_from_user(
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_user_by_path)
) -> AppointmentPublic:
    return appointment


@router.put(
    "/{username}",
    response_model=AppointmentPublic,
    name="appointments:confirm-appointment-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_appointment_confirmation_permissions)]
)
async def confirm_appointment_from_user(
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_user_by_path),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository))
) -> AppointmentPublic:
    return await appointments_repo.confirm_appointment(
        appointment=appointment
    )


@router.put(
    "/",
    response_model=AppointmentPublic,
    name="appointments:cancel-appointment-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_appointment_cancel_permissions)]
)
async def cancel_appointment_from_user(
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_current_user),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository))
) -> AppointmentPublic:
    return await appointments_repo.cancel_appointment(
        appointment=appointment,
    )


@router.delete(
    "/",
    response_model=AppointmentPublic,
    name="appointments:withdraw-appointment-from-user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_appointment_withdrawal_permissions)]
)
async def withdraw_appointment_from_user(
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_current_user),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository))
) -> AppointmentPublic:
    withdrawn_appointment = await appointments_repo.withdraw_appointment(appointment=appointment)
    return await appointments_repo.populate_appointment(appointment=withdrawn_appointment)