from typing import List
from fastapi import HTTPException, Depends, status

from app.models.user import UserInDB
from app.models.service import ServiceInDB
from app.models.appointment import AppointmentInDB, AppointmentStatus

from app.db.repositories.appointments import AppointmentsRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.users import get_user_by_username_from_path
from app.api.dependencies.services import get_service_by_id_from_path, user_owns_service


async def get_appointment_for_service_from_user(
    *, user: UserInDB, service: ServiceInDB, appointments_repo: AppointmentsRepository
) -> AppointmentInDB:
    appointment = await appointments_repo.get_appointment_for_service_from_user(
        service=service, user=user
    )

    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    return appointment


async def get_appointment_for_service_from_user_by_path(
    user: UserInDB = Depends(get_user_by_username_from_path),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository))
) -> AppointmentInDB:
    return await get_appointment_for_service_from_user(
        user=user, service=service, appointments_repo=appointments_repo
    )


async def list_appointments_for_service_by_id_from_path(
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository))
) -> List[AppointmentInDB]:
    return await appointments_repo.list_appointments_for_service(service=service)


async def check_appointment_create_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> None:
    if user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users are unable to request appointments for service jobs they own.",
        )
    if await appointments_repo.get_appointment_for_service_from_user(service=service, user=current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users aren't allowed to request more than one appointment for a service job."
        )


def check_appointment_list_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServiceInDB = Depends(get_service_by_id_from_path)
) -> None:
    if not user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to access appointments."
        )


def check_appointment_get_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_user_by_path)
) -> None:
    if not user_owns_service(user=current_user, service=service) and appointment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unable to access appointment."
        )


def check_appointment_confirmation_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_user_by_path),
    existing_appointments: List[AppointmentInDB] = Depends(
        list_appointments_for_service_by_id_from_path)
) -> None:
    if not user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner of the service may confirm appointments."
        )

    if appointment.status != AppointmentStatus.requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only confirm appointments that are currently requested",
        )

    if AppointmentStatus.confirmed in [a.status for a in existing_appointments]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That service job already has a confirmed appointment."
        )


async def get_appointment_for_service_from_current_user(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentInDB:
    return await get_appointment_for_service_from_user(
        user=current_user,
        service=service,
        appointments_repo=appointments_repo
    )


def check_appointment_cancel_permissions(
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_current_user),
) -> None:
    if appointment.status != AppointmentStatus.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel appointments that have been confirmed",
        )


def check_appointment_withdrawal_permissions(
    appointment: AppointmentInDB = Depends(get_appointment_for_service_from_current_user),
) -> None:
    if appointment.status != AppointmentStatus.requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only withdraw currently requested appointments."
        )