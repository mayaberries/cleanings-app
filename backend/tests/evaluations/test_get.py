from typing import Callable, List
from statistics import mean
import pytest
import uuid
from httpx import AsyncClient
from fastapi import FastAPI, status

from app.models.services.service import ServiceInDB
from app.models.appointments.evaluation import EvaluationAggregate, EvaluationPublic
from app.models.auth.user import UserInDB
from tests._helpers.get_appointment import get_appointment_for

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())

class TestGetEvaluations:
    async def test_authenticated_user_can_get_evaluation_for_service(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            user_client_two: UserInDB,
            test_list_of_services_with_evaluated_appointment: List[ServiceInDB]
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)
        service = test_list_of_services_with_evaluated_appointment[0]
        appointment = await get_appointment_for(app, service, user_client_one)

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-appointment",
                service_id=service.id,
                appointment_id=appointment.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        evaluation = EvaluationPublic(**response.json())

        assert evaluation.appointment_id == appointment.id
        assert evaluation.service_id == service.id
        assert evaluation.cleaner_id == user_client_one.id

        assert "test headline" in evaluation.headline
        assert "test comment" in evaluation.comment
        assert evaluation.professionalism > 0 and evaluation.professionalism <= 5
        assert evaluation.completeness > 0 and evaluation.completeness <= 5
        assert evaluation.efficiency > 0 and evaluation.efficiency <= 5
        assert evaluation.overall_rating > 0 and evaluation.overall_rating <= 5

    async def test_authenticated_user_can_get_list_of_evals_for_cleaner(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            user_client_two: UserInDB,
            test_list_of_services_with_evaluated_appointment: List[ServiceInDB]
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:list-evaluations-for-cleaner",
                username=user_client_one.username
            )
        )

        assert response.status_code == status.HTTP_200_OK

        evaluations = [EvaluationPublic(**e) for e in response.json()]

        assert len(evaluations) > 1

        for evaluation in evaluations:
            assert evaluation.cleaner_id == user_client_one.id
            assert evaluation.overall_rating >= 0

    async def test_authenticated_user_can_get_aggregate_stats_for_cleaner(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            user_client_two: UserInDB,
            test_list_of_services_with_evaluated_appointment: List[ServiceInDB]
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:list-evaluations-for-cleaner",
                username=user_client_one.username
            )
        )
        assert response.status_code == status.HTTP_200_OK
        evaluations = [EvaluationPublic(**e) for e in response.json()]

        response = await authorized_client.get(
            app.url_path_for(
                "evaluations:get-stats-for-cleaner",
                username=user_client_one.username
            )
        )
        assert response.status_code == status.HTTP_200_OK
        stats = EvaluationAggregate(**response.json())

        assert len(evaluations) == stats.total_evaluations
        assert max([e.overall_rating for e in evaluations]) == stats.max_overall_rating
        assert min([e.overall_rating for e in evaluations]) == stats.min_overall_rating
        assert mean([e.overall_rating for e in evaluations]) == stats.avg_overall_rating
        assert (
                mean([e.professionalism for e in evaluations if e.professionalism is not None]
                     ) == stats.avg_professionalism
        )
        assert mean([e.completeness for e in evaluations if e.completeness is not None]
                    ) == stats.avg_completeness
        assert mean([e.efficiency for e in evaluations if e.efficiency is not None]
                    ) == stats.avg_efficiency
        assert len([e for e in evaluations if e.overall_rating == 1]) == stats.one_stars
        assert len([e for e in evaluations if e.overall_rating == 2]) == stats.two_stars
        assert len([e for e in evaluations if e.overall_rating == 3]) == stats.three_stars
        assert len([e for e in evaluations if e.overall_rating == 4]) == stats.four_stars
        assert len([e for e in evaluations if e.overall_rating == 5]) == stats.five_stars

    async def test_unauthenticated_user_forbidden_from_get_requests(
            self,
            app: FastAPI,
            client: AsyncClient,
            user_client_one: UserInDB,
            test_list_of_services_with_evaluated_appointment: List[ServiceInDB]
    ) -> None:
        service = test_list_of_services_with_evaluated_appointment[0]
        appointment = await get_appointment_for(app, service, user_client_one)

        response = await client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-appointment",
                service_id=service.id,
                appointment_id=appointment.id,
            )
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await client.get(
            app.url_path_for(
                "evaluations:list-evaluations-for-cleaner",
                username=user_client_one.username
            )
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
