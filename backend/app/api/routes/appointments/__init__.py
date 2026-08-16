from fastapi import APIRouter
from app.api.routes.appointments.appointments import router as appointments_router
from app.api.routes.appointments.evaluations import evaluation_router, evaluations_router
from app.api.routes.appointments.feed import router as feed_router
from app.api.routes.appointments.public_booking import router as public_booking_router

router = APIRouter()

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
router.include_router(
    public_booking_router, prefix="/public", tags=["public-booking"])