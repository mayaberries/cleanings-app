from fastapi import APIRouter
from app.api.routes.clinics.services import router as services_router
from app.api.routes.auth.users import router as users_router
from app.api.routes.profiles.profiles import router as owner_profiles_router
from app.api.routes.appointments.appointments import router as appointments_router
from app.api.routes.appointments.evaluations import evaluation_router, evaluations_router
from app.api.routes.appointments.feed import router as feed_router
from app.api.routes.clinics.clinics import router as clinics_router
from app.api.routes.clinics.clinic_api_keys import router as clinic_api_keys_router
from app.api.routes.appointments.public_booking import router as public_booking_router
from app.api.routes.profiles.pets import router as pets_router
from app.api.routes.clinics.clinic_pets import router as clinic_pets_router
from app.api.routes.clinics.clinic_availability import router as clinic_availability_router

router = APIRouter()

router.include_router(
    services_router, prefix="/services", tags=["services"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(owner_profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(
    appointments_router, prefix="/services/{service_id}/appointments", tags=["appointments"])
router.include_router(
    evaluation_router,
    prefix="/services/{service_id}/appointments/{appointment_id}/evaluation",
    tags=["evaluations"],
)
router.include_router(
    evaluations_router, prefix="/users/{username}/evaluations", tags=["evaluations"])
router.include_router(feed_router, prefix="/feed", tags=["feed"])
router.include_router(clinics_router, prefix="/clinics", tags=["clinics"])
router.include_router(
    clinic_api_keys_router, prefix="/clinics/{clinic_id}/api-keys", tags=["clinic-api-keys"])
router.include_router(
    public_booking_router, prefix="/public", tags=["public-booking"])
router.include_router(
    pets_router, prefix="/pets", tags=["pets"]
)
router.include_router(
    clinic_pets_router, prefix="/clinic_pets", tags=["clinic_pets"]
)
router.include_router(
    clinic_availability_router, prefix="/clinics/{clinic_id}/availability", tags=["clinic-availability"])
