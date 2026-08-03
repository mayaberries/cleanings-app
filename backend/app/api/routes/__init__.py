from fastapi import APIRouter
from app.api.routes.services import router as services_router
from app.api.routes.users import router as users_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.offers import router as offers_router
from app.api.routes.evaluations import router as evaluations_router
from app.api.routes.feed import router as feed_router

router = APIRouter()

router.include_router(
    services_router, prefix="/services", tags=["services"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
router.include_router(
    offers_router, prefix="/services/{service_id}/offers", tags=["offers"])
router.include_router(
    evaluations_router, prefix="/users/{username}/evaluations", tags=["evaluations"])
router.include_router(feed_router, prefix="/feed", tags=["feed"])
