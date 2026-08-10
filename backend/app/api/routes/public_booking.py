from datetime import timedelta
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import EmailStr
from starlette.status import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_201_CREATED

from app.api.dependencies.database import get_repository
from app.api.dependencies.public_auth import get_clinic_from_public_key
from app.core.limiter import enforce_public_rate_limits
from app.db.repositories.appointments import AppointmentsRepository
from app.db.repositories.clinic_owner_profiles import ClinicOwnerProfilesRepository
from app.db.repositories.pets import PetProfilesRepository
from app.db.repositories.services import ServicesRepository
from app.db.repositories.users import UsersRepository
from app.models.appointments.appointment import (
    PublicAppointmentCreate,
    AppointmentCreate,
    AppointmentPublic,
    DEFAULT_APPOINTMENT_DURATION_MINUTES,
)
from app.models.clinics.clinic import ClinicInDB
from app.models.clinics.clinic_owner_profile import ClinicOwnerProfileRegistration
from app.models.profiles.pet_profile import PetProfilePublic
from app.models.services.service import ServicePublic

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


@router.get("/pets", response_model=List[PetProfilePublic], name="public-booking:list-pets")
async def list_public_pets(
        email: EmailStr = Query(...),
        clinic: ClinicInDB = Depends(get_clinic_from_public_key),
        users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> List[PetProfilePublic]:
    """
    'Log in as the owner' for a widget with no login: the email the guest
    types in is the only credential there is. Always 200 + [] rather than
    404 for an unknown email/owner/pivot -- this must never confirm or
    deny whether a given email has booked with this clinic before.
    """
    user = await users_repo.get_user_by_email(email=email, populate=False)
    if not user:
        return []

    owner_profile = await users_repo.profiles_repo.get_profile_by_user_id(user_id=user.id)
    if not owner_profile:
        return []

    pivot = await pivots_repo.get_pivot_for_clinic_and_owner(
        clinic_id=clinic.id, owner_profile_id=owner_profile.id
    )
    if not pivot:
        return []

    return await pets_repo.list_pet_profiles_for_clinic(
        clinic_id=clinic.id, owner_profile_id=owner_profile.id
    )


@router.post("/appointments", response_model=AppointmentPublic,
             name="public-booking:create-appointment", status_code=HTTP_201_CREATED)
async def create_public_appointment(
        appointment_in: PublicAppointmentCreate = Body(..., embed=False),
        clinic: ClinicInDB = Depends(get_clinic_from_public_key),
        services_repo: ServicesRepository = Depends(get_repository(ServicesRepository)),
        appointments_repo: AppointmentsRepository = Depends(get_repository(AppointmentsRepository)),
        users_repo: UsersRepository = Depends(get_repository(UsersRepository)),
        pivots_repo: ClinicOwnerProfilesRepository = Depends(get_repository(ClinicOwnerProfilesRepository)),
        pets_repo: PetProfilesRepository = Depends(get_repository(PetProfilesRepository)),
) -> AppointmentPublic:
    service = await services_repo.get_service_by_id_for_clinic(
        id=appointment_in.service_id, clinic_id=clinic.id
    )
    if not service:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail="No bookable service found with that id for this clinic.")

    duration = service.duration_minutes or DEFAULT_APPOINTMENT_DURATION_MINUTES
    end_time = appointment_in.start_time + timedelta(minutes=duration)

    if await appointments_repo.has_overlapping_confirmed_appointment(
            clinic_id=clinic.id, start_time=appointment_in.start_time, end_time=end_time
    ):
        raise HTTPException(status_code=HTTP_409_CONFLICT,
                            detail="That time is no longer available. Please choose another slot.")

    guest_user = await users_repo.get_or_create_guest_user(
        email=appointment_in.email,
        full_name=appointment_in.full_name,
        phone_number=appointment_in.phone_number,
    )
    owner_profile = await users_repo.profiles_repo.get_profile_by_user_id(user_id=guest_user.id)

    # Fixes the previously-missing registration: every public booking
    # now (idempotently) links the guest owner to this clinic, which is
    # what makes GET /public/pets and the clinic dashboard see them at
    # all, on this and every future visit.
    await pivots_repo.register_owner_profile_with_clinic(
        clinic_id=clinic.id,
        registration=ClinicOwnerProfileRegistration(owner_profile_id=owner_profile.id),
    )

    if appointment_in.pet.pet_id is not None:
        pet = await pets_repo.get_pet_by_id_for_clinic(id=appointment_in.pet.pet_id, clinic_id=clinic.id)
        # Must belong to *this* guest, not just any owner registered at
        # this clinic -- get_pet_by_id_for_clinic alone doesn't check that.
        if not pet or pet.owner_profile_id != owner_profile.id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                                detail="No pet found with that id for this clinic.")
    else:
        pet = await pets_repo.create_pet(new_pet=appointment_in.pet.new_pet, owner_profile_id=owner_profile.id)

    created_appointment = await appointments_repo.create_appointment_for_service(
        new_appointment=AppointmentCreate(
            user_id=guest_user.id,
            pet_id=pet.id,
            service_id=service.id,
            start_time=appointment_in.start_time,
        ),
        service=service,
    )

    return await appointments_repo.populate_appointment(appointment=created_appointment)
