from datetime import timedelta
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_501_NOT_IMPLEMENTED, HTTP_201_CREATED

from app.core.limiter import enforce_public_rate_limits
from app.api.dependencies.public_auth import get_clinic_from_public_key
from app.api.dependencies.database import get_repository
from app.models.clinic import ClinicInDB
from app.models.service import ServicePublic
from app.models.appointment import (
    PublicAppointmentCreate,
    AppointmentCreate,
    AppointmentPublic,
    DEFAULT_APPOINTMENT_DURATION_MINUTES,
)
from app.db.repositories.services import ServicesRepository
from app.db.repositories.appointments import AppointmentsRepository
from app.db.repositories.users import UsersRepository

# Rate limiting applied once, router-wide, rather than per-route -- see
# app/core/limiter.py for why this replaced two stacked slowapi decorators.
# Ordered before get_clinic_from_public_key deliberately: an over-budget
# caller gets rejected before we even touch the DB for key lookup.
router = APIRouter(dependencies=[Depends(enforce_public_rate_limits)])


@router.get("/services", response_model=List[ServicePublic], name="public-booking:list-services")
async def list_bookable_services(
    clinic: ClinicInDB = Depends(get_clinic_from_public_key),
    services_repo: ServicesRepository = Depends(get_repository(ServicesRepository)),
) -> List[ServicePublic]:
    return await services_repo.list_services_by_clinic_id(clinic_id=clinic.id)


@router.get("/availability", name="public-booking:get-availability")
async def get_availability(
    clinic: ClinicInDB = Depends(get_clinic_from_public_key),
) -> None:
    """
    TODO (steps 3-7): given ?service_id=&date=, compute open slots for the
    resolved clinic -- operating hours, staff/resource capacity, and
    existing confirmed appointments (has_overlapping_confirmed_appointment,
    generalized from a single point-in-time check into an actual slot
    generator -- no such generator exists yet anywhere in the repo).

    Auth + rate limiting are already fully in effect on this route --
    nothing here changes when the real logic is added. create_public_
    appointment below already reuses has_overlapping_confirmed_appointment
    directly, so whatever slot generator lands here should stay consistent
    with that same conflict definition rather than inventing a second one.
    """
    raise HTTPException(
        status_code=HTTP_501_NOT_IMPLEMENTED,
        detail="Availability calculation is not implemented yet.",
    )


@router.post(
    "/appointments",
    response_model=AppointmentPublic,
    name="public-booking:create-appointment",
    status_code=HTTP_201_CREATED,
)
async def create_public_appointment(
    appointment_in: PublicAppointmentCreate = Body(..., embed=False),
    clinic: ClinicInDB = Depends(get_clinic_from_public_key),
    services_repo: ServicesRepository = Depends(get_repository(ServicesRepository)),
    appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
    users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
) -> AppointmentPublic:
    service = await services_repo.get_service_by_id_for_clinic(
        id=appointment_in.service_id, clinic_id=clinic.id
    )
    if not service:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No bookable service found with that id for this clinic.",
        )

    duration = service.duration_minutes or DEFAULT_APPOINTMENT_DURATION_MINUTES
    end_time = appointment_in.start_time + timedelta(minutes=duration)

    # Same conflict check the JWT-authed appointment flow relies on --
    # reused as-is rather than reimplemented, so "is this slot free" means
    # exactly one thing across both entry points. Doesn't fully replace a
    # real availability endpoint (a client could still guess/POST a dozen
    # slots to find an open one), but it's the actual source of truth for
    # whether a booking succeeds either way.
    has_conflict = await appointments_repo.has_overlapping_confirmed_appointment(
        clinic_id=clinic.id, start_time=appointment_in.start_time, end_time=end_time
    )
    if has_conflict:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail="That time is no longer available. Please choose another slot.",
        )

    guest_user = await users_repo.get_or_create_guest_user(
        email=appointment_in.email,
        full_name=appointment_in.full_name,
        phone_number=appointment_in.phone_number,
    )

    created_appointment = await appointments_repo.create_appointment_for_service(
        new_appointment=AppointmentCreate(
            user_id=guest_user.id,
            service_id=service.id,
            start_time=appointment_in.start_time,
        ),
        service=service,
    )

    return await appointments_repo.populate_appointment(appointment=created_appointment)