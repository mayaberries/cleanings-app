from fastapi import APIRouter
from app.api.routes.services import router as services_router
from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.appointments import router as appointments_router
from app.api.routes.evaluations import evaluation_router, evaluations_router
from app.api.routes.feed import router as feed_router
from app.api.routes.clinics import router as clinics_router
from app.api.routes.clinic_api_keys import router as clinic_api_keys_router
from app.api.routes.public_booking import router as public_booking_router
from app.api.routes.pets import router as pets_router
from app.api.routes.clinic_pets import router as clinic_pets_router

router = APIRouter()

router.include_router(
    services_router, prefix="/services", tags=["services"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
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
