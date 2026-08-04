from typing import List
from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette import status

from app.api.dependencies.appointments import get_appointment_for_service_from_user_by_path
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.services import get_service_by_id_from_path, user_owns_service
from app.api.dependencies.database import get_repository
from app.api.dependencies.users import get_user_by_username_from_path
from app.db.repositories.evaluations import EvaluationsRepository
from app.models.service import ServiceInDB
from app.models.appointment import AppointmentInDB, AppointmentStatus
from app.models.user import UserInDB
from app.models.evaluation import EvaluationInDB


async def check_evaluation_create_permissions(
    current_user: UserInDB = Depends(get_current_active_user),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    cleaner: UserInDB = Depends(get_user_by_username_from_path),
    offer: AppointmentInDB = Depends(get_appointment_for_service_from_user_by_path),
    evals_repo: EvaluationsRepository = Depends(
        get_repository(EvaluationsRepository))
) -> None:
    if not user_owns_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are unable to leave evaluations for service jobs they do not own."
        )

    if offer.status != AppointmentStatus.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only users with accepted offers can be evaluated"
        )
    
    if offer.user_id != cleaner.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not authorized to leave an evaluation for this user."
        )


async def list_evaluations_for_cleaner_from_path(
    cleaner: UserInDB = Depends(get_user_by_username_from_path),
    evals_repo: EvaluationsRepository = Depends(
        get_repository(EvaluationsRepository))
) -> List[EvaluationInDB]:
    return await evals_repo.list_evaluations_for_cleaner(cleaner=cleaner)


async def get_cleaner_evaluation_for_service_from_path(
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    cleaner: UserInDB = Depends(get_user_by_username_from_path),
    evals_repo: EvaluationsRepository = Depends(
        get_repository(EvaluationsRepository))
):
    evaluation = await evals_repo.get_cleaner_evaluation_for_service(service=service, cleaner=cleaner)

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evaluation found for service ${service.id}"
        )

    return evaluation
