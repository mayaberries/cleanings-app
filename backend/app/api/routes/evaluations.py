from typing import List
from fastapi import APIRouter, Body, status
from fastapi.param_functions import Depends

from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB, EvaluationPublic
from app.models.appointment import AppointmentInDB
from app.models.user import UserInDB

from app.api.dependencies.database import get_repository
from app.api.dependencies.appointments import get_appointment_by_id_from_path
from app.api.dependencies.users import get_user_by_username_from_path

from app.db.repositories.evaluations import EvaluationsRepository
from app.api.dependencies.evaluations import (
    check_evaluation_create_permissions,
    get_evaluation_for_appointment_from_path,
    list_evaluations_for_cleaner_from_path,
)

# Mounted at /services/{service_id}/appointments/{appointment_id}/evaluation
evaluation_router = APIRouter()


@evaluation_router.post(
    "/",
    response_model=EvaluationPublic,
    name="evaluations:create-evaluation-for-appointment",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_evaluation_create_permissions)]
)
async def create_evaluation_for_appointment(
        evaluation_create: EvaluationCreate = Body(..., embed=False),
        appointment: AppointmentInDB = Depends(get_appointment_by_id_from_path),
        eval_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository))
) -> EvaluationPublic:
    return await eval_repo.create_evaluation_for_appointment(
        evaluation_create=evaluation_create, appointment=appointment
    )


@evaluation_router.get(
    "/",
    response_model=EvaluationPublic,
    name="evaluations:get-evaluation-for-appointment",
    status_code=status.HTTP_200_OK,
)
async def get_evaluation_for_appointment(
        evaluation: EvaluationInDB = Depends(get_evaluation_for_appointment_from_path)
) -> EvaluationPublic:
    return evaluation


# Mounted at /users/{username}/evaluations
evaluations_router = APIRouter()


@evaluations_router.get(
    "/",
    response_model=List[EvaluationPublic],
    name="evaluations:list-evaluations-for-cleaner",
    status_code=status.HTTP_200_OK,
)
async def list_evaluations_for_cleaner(
        evaluations: List[EvaluationInDB] = Depends(list_evaluations_for_cleaner_from_path)
) -> List[EvaluationPublic]:
    return evaluations


@evaluations_router.get(
    "/stats",
    response_model=EvaluationAggregate,
    name="evaluations:get-stats-for-cleaner",
    status_code=status.HTTP_200_OK
)
async def get_stats_for_cleaner(
        cleaner: UserInDB = Depends(get_user_by_username_from_path),
        evals_repo: EvaluationsRepository = Depends(get_repository(EvaluationsRepository))
) -> EvaluationAggregate:
    return await evals_repo.get_cleaner_aggregates(cleaner=cleaner)
