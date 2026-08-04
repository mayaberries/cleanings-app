import uuid
from typing import Callable

import pytest
from fastapi import FastAPI, status

from app.models.evaluation import EvaluationCreate, EvaluationInDB
from app.models.service import ServiceInDB
from app.models.user import UserInDB
from tests._helpers.get_appointment import get_appointment_for

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


class TestCreateEvaluations:
    async def test_owner_can_leave_evaluation_for_cleaner_and_mark_offer_completed(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_clinic_a_admin: UserInDB,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB,
    ) -> None:
        evaluation_create = EvaluationCreate(
            no_show=False,
            headline="Excellent Job",
            comment="Really appreciated the hard work and effort they put into this job!",
            professionalism=5,
            completeness=5,
            efficiency=4,
            overall_rating=5
        )

        authorized_client = create_authorized_client(user=user_clinic_a_admin)
        appointment = await get_appointment_for(app, test_service_with_accepted_appointment, user_client_one)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=appointment.id,
            ),
            json=evaluation_create.model_dump()
        )

        assert response.status_code == status.HTTP_201_CREATED

        evaluation = EvaluationInDB(**response.json())

        assert evaluation.appointment_id == appointment.id
        assert evaluation.no_show == evaluation_create.no_show
        assert evaluation.headline == evaluation_create.headline
        assert evaluation.overall_rating == evaluation_create.overall_rating

        response = await authorized_client.get(
            app.url_path_for(
                "appointments:get-appointment-by-id",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=appointment.id,
            ),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "completed"

    async def test_non_owner_cant_leave_evaluation_for(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            user_client_two: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)
        appointment = await get_appointment_for(app, test_service_with_accepted_appointment, user_client_one)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=appointment.id,
            ),
            json={"overall_rating": 2}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_owner_cant_leave_multiple_evaluation(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_clinic_a_admin: UserInDB,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_clinic_a_admin)
        appointment = await get_appointment_for(app, test_service_with_accepted_appointment, user_client_one)

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=appointment.id,
            ),
            json={"overall_rating": 2}
        )

        assert response.status_code == status.HTTP_201_CREATED

        response = await authorized_client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=appointment.id,
            ),
            json={"overall_rating": 1}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
