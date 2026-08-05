from typing import List
from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette import status

from app.api.dependencies.appointments import get_appointment_by_id_from_path
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.services import get_service_by_id_from_path, user_can_manage_service
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
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        evals_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository))
) -> None:
    if not user_can_manage_service(user=current_user, service=service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users are unable to leave evaluations for service jobs they do not own."
        )

    if appointment.status != AppointmentStatus.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed appointments can be evaluated"
        )

    if await evals_repo.get_evaluation_for_appointment(appointment_id=appointment.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An evaluation already exists for this appointment."
        )


async def list_evaluations_for_cleaner_from_path(
        cleaner: UserInDB = Depends(get_user_by_username_from_path),
        evals_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository))
) -> List[EvaluationInDB]:
    return await evals_repo.list_evaluations_for_cleaner(cleaner=cleaner)


async def get_evaluation_for_appointment_from_path(
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        evals_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository))
) -> EvaluationInDB:
    evaluation = await evals_repo.get_evaluation_for_appointment(appointment_id=appointment.id)

    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evaluation found for appointment {appointment.id}"
        )

    return evaluation
