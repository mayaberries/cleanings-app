from fastapi import APIRouter
from app.api.routes.clinics.services import router as services_router
from app.api.routes.clinics.clinics import router as clinics_router
from app.api.routes.clinics.clinic_api_keys import router as clinic_api_keys_router
from app.api.routes.clinics.clinic_owner_profiles import router as clinic_owner_profiles_router
from app.api.routes.clinics.clinic_pets import router as clinic_pets_router
from app.api.routes.clinics.clinic_availability import router as clinic_availability_router

router = APIRouter()

router.include_router(
    services_router, prefix="/services", tags=["services"])
router.include_router(clinics_router, prefix="/clinics", tags=["clinics"])
router.include_router(
    clinic_api_keys_router, prefix="/clinics/{clinic_id}/api-keys", tags=["clinic-api-keys"])
router.include_router(
    clinic_owner_profiles_router, prefix="/clinic_owners", tags=["clinic_owners"]
)
router.include_router(
    clinic_pets_router, prefix="/clinic_pets", tags=["clinic_pets"]
)
router.include_router(
    clinic_availability_router, prefix="/clinics/{clinic_id}/availability", tags=["clinic-availability"])