from typing import Callable, List
from statistics import mean
import pytest
import uuid
from httpx import AsyncClient
from fastapi import FastAPI, status
from app.models.service import ServiceInDB
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB, EvaluationPublic

from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


class TestEvaluationRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.post(app.url_path_for("evaluations:create-evaluation-for-cleaner", service_id=FAKE_ID, username="braddpit"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("evaluations:get-evaluation-for-cleaner", service_id=FAKE_ID,  username="braddpit"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("evaluations:list-evaluations-for-cleaner", username="bradpitt"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("evaluations:get-stats-for-cleaner", username="bradpitt"))
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestCreateEvaluations:
    async def test_owner_can_leave_evaluation_for_cleaner_and_mark_offer_completed(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_darlene: UserInDB,
        user_mr_robot: UserInDB,
        test_service_with_accepted_offer: ServiceInDB,
    ) -> None:
        evaluation_create = EvaluationCreate(
            no_show=False,
            headline="Excellent Job",
            comment=f"""
Really appreciated the hard work and effort they put into this job!
Though the cleaner took their time, I would definitely hire them again for the quality of their work.
            """,
            professionalism=5,
            completeness=5,
            efficiency=4,
            overall_rating=5
        )

        authorized_client = create_authorized_client(user=user_darlene)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                service_id=test_service_with_accepted_offer.id,
                username=user_mr_robot.username
            ),
            json=evaluation_create.model_dump()
        )

        assert response.status_code == status.HTTP_201_CREATED

        evaluation = EvaluationInDB(**response.json())

        assert evaluation.no_show == evaluation_create.no_show
        assert evaluation.headline == evaluation_create.headline
        assert evaluation.overall_rating == evaluation_create.overall_rating

        response = await authorized_client.get(
            app.url_path_for(
                "offers:get-offer-from-user",
                service_id=test_service_with_accepted_offer.id,
                username=user_mr_robot.username
            ),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "completed"

    async def test_non_owner_cant_leave_evaluation_for(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_mr_robot: UserInDB,
        user_tyrell: UserInDB,
        test_service_with_accepted_offer: ServiceInDB,
    ) -> None:

        authorized_client = create_authorized_client(user=user_tyrell)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                service_id=test_service_with_accepted_offer.id,
                username=user_mr_robot.username
            ),
            json={"overall_rating": 2}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_owner_cant_leave_evaluation_for_wrong_user(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_darlene: UserInDB,
        user_tyrell: UserInDB,
        test_service_with_accepted_offer: ServiceInDB,
    ) -> None:

        authorized_client = create_authorized_client(user=user_darlene)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                service_id=test_service_with_accepted_offer.id,
                username=user_tyrell.username
            ),
            json={"overall_rating": 2}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_owner_cant_leave_multiple_evaluation(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_darlene: UserInDB,
        user_mr_robot: UserInDB,

        test_service_with_accepted_offer: ServiceInDB,
    ) -> None:

        authorized_client = create_authorized_client(user=user_darlene)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                service_id=test_service_with_accepted_offer.id,
                username=user_mr_robot.username
            ),
            json={"overall_rating": 2}
        )

        assert response.status_code == status.HTTP_201_CREATED

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-cleaner",
                service_id=test_service_with_accepted_offer.id,
                username=user_mr_robot.username
            ),
            json={"overall_rating": 1}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetEvaluations:
    async def test_authenticated_user_can_get_evaluation_for_service(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_mr_robot: UserInDB,
        user_tyrell: UserInDB,
        test_list_of_services_with_evaluated_offer: List[ServiceInDB]
    ) -> None:
        authorized_client = create_authorized_client(user=user_tyrell)

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-cleaner",
                service_id=test_list_of_services_with_evaluated_offer[0].id,
                username=user_mr_robot.username
            )
        )

        assert response.status_code == status.HTTP_200_OK

        evaluation = EvaluationPublic(**response.json())

        assert evaluation.service_id == test_list_of_services_with_evaluated_offer[0].id
        assert evaluation.cleaner_id == user_mr_robot.id

        assert "test headline" in evaluation.headline
        assert "test comment" in evaluation.comment
        # TODO: Modify model to accept only evals from 1 to 5 stars
        assert evaluation.professionalism > 0 and evaluation.professionalism <= 5
        assert evaluation.completeness > 0 and evaluation.completeness <= 5
        assert evaluation.efficiency > 0 and evaluation.efficiency <= 5
        assert evaluation.overall_rating > 0 and evaluation.overall_rating <= 5

    async def test_authenticated_user_can_get_list_of_evals_for_cleaner(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_mr_robot: UserInDB,
        user_tyrell: UserInDB,
        test_list_of_services_with_evaluated_offer: List[ServiceInDB]
    ) -> None:
        authorized_client = create_authorized_client(user=user_tyrell)

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:list-evaluations-for-cleaner",
                username=user_mr_robot.username
            )
        )

        assert response.status_code == status.HTTP_200_OK

        evaluations = [EvaluationPublic(**e) for e in response.json()]

        assert len(evaluations) > 1

        for evaluation in evaluations:
            assert evaluation.cleaner_id == user_mr_robot.id
            assert evaluation.overall_rating >= 0

    async def test_authenticated_user_can_get_aggregate_stats_for_cleaner(
        self,
        app: FastAPI,
        create_authorized_client: Callable,
        user_mr_robot: UserInDB,
        user_tyrell: UserInDB,
        test_list_of_services_with_evaluated_offer: List[ServiceInDB]
    ) -> None:
        authorized_client = create_authorized_client(user=user_tyrell)

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:list-evaluations-for-cleaner",
                username=user_mr_robot.username
            )
        )
        assert response.status_code == status.HTTP_200_OK
        evaluations = [EvaluationPublic(**e) for e in response.json()]

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:get-stats-for-cleaner",
                username=user_mr_robot.username
            )
        )
        assert response.status_code == status.HTTP_200_OK
        stats = EvaluationAggregate(**response.json())

        assert len(evaluations) == stats.total_evaluations
        assert max([e.overall_rating for e in evaluations]
                   ) == stats.max_overall_rating
        assert min([e.overall_rating for e in evaluations]
                   ) == stats.min_overall_rating
        assert mean([e.overall_rating for e in evaluations]
                    ) == stats.avg_overall_rating
        assert(
            mean([e.professionalism for e in evaluations if e.professionalism is not None]
                 ) == stats.avg_professionalism
        )
        assert mean([e.completeness for e in evaluations if e.completeness is not None]
                    ) == stats.avg_completeness

        assert mean([e.efficiency for e in evaluations if e.efficiency is not None]
                    ) == stats.avg_efficiency
        assert len([e for e in evaluations if e.overall_rating == 1]
                   ) == stats.one_stars
        assert len([e for e in evaluations if e.overall_rating == 2]
                   ) == stats.two_stars
        assert len([e for e in evaluations if e.overall_rating == 3]
                   ) == stats.three_stars
        assert len([e for e in evaluations if e.overall_rating == 4]
                   ) == stats.four_stars
        assert len([e for e in evaluations if e.overall_rating == 5]
                   ) == stats.five_stars

    async def test_unauthenticated_user_forbidden_from_get_requests(
        self,
        app: FastAPI,
        client: AsyncClient,
        user_mr_robot: UserInDB,
        test_list_of_services_with_evaluated_offer: List[ServiceInDB]
    ) -> None:
        response = await client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-cleaner",
                service_id=test_list_of_services_with_evaluated_offer[0].id,
                username=user_mr_robot.username,
            )
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.get(
            app.url_path_for(
                "evaluations:list-evaluations-for-cleaner",
                username=user_mr_robot.username
            )
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
