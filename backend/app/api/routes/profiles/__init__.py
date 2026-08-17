from fastapi import APIRouter
from app.api.routes.profiles.profiles import router as owner_profiles_router
from app.api.routes.profiles.pets import router as pets_router

router = APIRouter()

router.include_router(owner_profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(
    pets_router, prefix="/pets", tags=["pets"]
)