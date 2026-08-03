from re import M
from typing import List
from fastapi import APIRouter, Path, Body, status, HTTPException
from fastapi.param_functions import Depends

from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationUpdate, EvaluationInDB, EvaluationPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

from app.api.dependencies.database import get_repository
from app.api.dependencies.services import get_service_by_id_from_path
from app.api.dependencies.users import get_user_by_username_from_path

from app.db.repositories.evaluations import EvaluationsRepository
from app.api.dependencies.evaluations import check_evaluation_create_permissions, get_cleaner_evaluation_for_service_from_path, list_evaluations_for_cleaner_from_path


router = APIRouter()


@router.post(
    "/{service_id}",
    response_model=EvaluationPublic,
    name="evaluations:create-evaluation-for-cleaner",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_evaluation_create_permissions)]
)
async def create_evaluation_for_cleaner(
    evaluation_create: EvaluationCreate = Body(..., embed=False),
    service: ServiceInDB = Depends(get_service_by_id_from_path),
    cleaner: UserInDB = Depends(get_user_by_username_from_path),
    eval_repo: EvaluationsRepository = Depends(
        get_repository(EvaluationsRepository))
) -> EvaluationPublic:
    return await eval_repo.create_evaluation_for_cleaner(
        evaluation_create=evaluation_create, cleaner=cleaner, service=service
    )


@router.get(
    "/",
    response_model=List[EvaluationPublic],
    name="evaluations:list-evaluations-for-cleaner",
    status_code=status.HTTP_200_OK,
)
async def list_evaluation_for_service(
    evaluations: List[EvaluationInDB] = Depends(
        list_evaluations_for_cleaner_from_path)
) -> List[EvaluationPublic]:
    return evaluations

# Important note! The order in which we define these routes ABSOLUTELY DOES
# MATTER. If we were to put the /stats/ route after our
# evaluations:get-evaluation-for-cleaner route, that stats route wouldn't
# work. FastAPI would assume that "stats" is the ID of a service and throw a 422
# error since "stats" is not an integer id.


@router.get(
    "/stats",
    response_model=EvaluationAggregate,
    name="evaluations:get-stats-for-cleaner",
    status_code=status.HTTP_200_OK
)
async def get_evaluation_from_user(
    cleaner: UserInDB = Depends(get_user_by_username_from_path),
    evals_repo: EvaluationsRepository = Depends(
        get_repository(EvaluationsRepository))
) -> EvaluationPublic:
    return await evals_repo.get_cleaner_aggregates(cleaner=cleaner)


@router.get(
    "/{service_id}",
    response_model=EvaluationPublic,
    name="evaluations:get-evaluation-for-cleaner",
    status_code=status.HTTP_200_OK
)
async def create_evaluation_for_cleaner(
    evaluation: EvaluationInDB = Depends(
        get_cleaner_evaluation_for_service_from_path)
) -> EvaluationPublic:
    return evaluation
