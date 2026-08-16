from fastapi import APIRouter
from app.api.routes.appointments import router as appointments_router
from app.api.routes.auth import router as auth_router
from app.api.routes.clinics import router as clinics_router
from app.api.routes.profiles import router as profiles_router

router = APIRouter()

router.include_router(appointments_router)
router.include_router(auth_router)
router.include_router(clinics_router)
router.include_router(profiles_router)