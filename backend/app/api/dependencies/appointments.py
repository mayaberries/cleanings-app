from fastapi import HTTPException, Depends, Path, status

from app.models.user import UserInDB
from app.models.service import ServiceInDB
from app.models.appointment import AppointmentInDB, AppointmentStatus

from app.db.repositories.appointments import AppointmentsRepository

from app.api.dependencies.database import get_repository
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.services import get_service_by_id_from_path, user_owns_service
from app.api.dependencies.users import get_user_by_username_from_path


async def get_appointment_for_service_from_user_by_path(
        user: UserInDB = Depends(get_user_by_username_from_path),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentInDB:
    """
    TEMPORARY shim, kept only so evaluations.py can still import something.
    Evaluations currently assume one appointment per (service, user) pair,
    which is no longer true post-phase-2 — a client can have several
    appointments for the same service. This returns the most recent one
    as a stopgap. Do not build new functionality on top of this; it goes
    away when evaluations move to being keyed by appointment_id (phase 3).
    """
    appointments = await appointments_repo.list_appointments_for_service_from_user(service=service, user=user)

    if not appointments:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    return appointments[0]  # most recent — repo query orders by start_time DESC


async def get_appointment_by_id_from_path(
        appointment_id: str = Path(...),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> AppointmentInDB:
    appointment = await appointments_repo.get_appointment_by_id(id=appointment_id)

    if not appointment or appointment.service_id != service.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    return appointment


def check_appointment_create_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
) -> None:
    if user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users are unable to request appointments for services they own.",
        )


def check_appointment_list_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
) -> None:
    if not user_owns_service(user=current_user, service=service):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to access appointments.")


def check_appointment_get_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
) -> None:
    if not user_owns_service(user=current_user, service=service) and appointment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to access appointment.")


async def check_appointment_confirmation_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> None:
    if not user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner of the service may confirm appointments.",
        )

    if appointment.status != AppointmentStatus.requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only confirm appointments that are currently requested",
        )

    owner_id = service.owner if isinstance(service.owner, str) else service.owner.id

    if await appointments_repo.has_overlapping_confirmed_appointment(owner=owner_id, appointment=appointment):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This time conflicts with another confirmed appointment.",
        )


def check_appointment_cancel_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
) -> None:
    if appointment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to cancel this appointment.")
    if appointment.status != AppointmentStatus.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel appointments that have been confirmed",
        )


def check_appointment_withdrawal_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
) -> None:
    if appointment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to withdraw this appointment.")
    if appointment.status != AppointmentStatus.requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only withdraw currently requested appointments.",
        )
