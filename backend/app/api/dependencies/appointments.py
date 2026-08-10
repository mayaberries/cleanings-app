from datetime import timedelta

from fastapi import HTTPException, Depends, Path, status, Body

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.api.dependencies.pets import get_owner_profile_id_for_user
from app.api.dependencies.services import get_service_by_id_from_path, user_can_manage_service, get_service_clinic_id
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.appointments import AppointmentsRepository
from app.db.repositories.pets import PetProfilesRepository
from app.models.appointments.appointment import AppointmentInDB, AppointmentStatus, DEFAULT_APPOINTMENT_DURATION_MINUTES, \
    AppointmentRequestIn
from app.models.services.service import ServiceInDB
from app.models.auth.user import UserInDB


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


async def check_appointment_create_permissions(
        appointment_in: AppointmentRequestIn = Body(..., embed=False),
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> None:
    if user_can_manage_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Users are unable to request appointments for services they own.",
        )

    # NEW — same 404-not-403 opacity as the pet/owner dependencies
    # elsewhere: don't confirm whether a given pet_id exists at all if it
    # isn't the requesting user's own.
    pet = await pets_repo.get_pet_by_id(id=appointment_in.pet_id)
    if not pet or pet.owner_profile_id != get_owner_profile_id_for_user(user=current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pet found with that id.",
        )

    clinic_id = get_service_clinic_id(service)
    duration = service.duration_minutes or DEFAULT_APPOINTMENT_DURATION_MINUTES
    end_time = appointment_in.start_time + timedelta(minutes=duration)

    if await appointments_repo.has_overlapping_confirmed_appointment(
            clinic_id=clinic_id, start_time=appointment_in.start_time, end_time=end_time
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This time is already booked.")


def check_appointment_list_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
) -> None:
    if not user_can_manage_service(user=current_user, service=service):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to access appointments.")


def check_appointment_get_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
) -> None:
    if not user_can_manage_service(user=current_user, service=service) and appointment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to access appointment.")


async def check_appointment_confirmation_permissions(
        current_user: UserInDB = Depends(get_current_active_user),
        service: ServiceInDB = Depends(get_service_by_id_from_path),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
) -> None:
    if not user_can_manage_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only staff of the clinic that owns this service may confirm appointments.",
        )

    if appointment.status != AppointmentStatus.requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only confirm appointments that are currently requested",
        )

    clinic_id = get_service_clinic_id(service)

    if await appointments_repo.has_overlapping_confirmed_appointment(
            clinic_id=clinic_id,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            exclude_id=appointment.id,
    ):
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
