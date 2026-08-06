from fastapi import APIRouter
from app.api.routes.services import router as services_router
from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.appointments import router as appointments_router
from app.api.routes.evaluations import evaluation_router, evaluations_router
from app.api.routes.feed import router as feed_router
from app.api.routes.clinics import router as clinics_router
from app.api.routes.clinic_owner_profiles import router as clinic_owner_profiles_router
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
router.include_router(clinic_owner_profiles_router, prefix="/clinic/owners", tags=["clinic_owners"])
router.include_router(clinic_pets_router, prefix="/clinic/pets", tags=["clinic_pets"])
