import datetime
import uuid
from typing import Callable

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.appointment import AppointmentPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


def future_time(hours: int = 1) -> str:
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).isoformat()


class TestCreateAppointments:
    async def test_user_can_successfully_create_offer_for_other_users_service_job(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_one: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )
        assert response.status_code == status.HTTP_201_CREATED

        offer = AppointmentPublic(**response.json())
        assert offer.user_id == user_client_one.id
        assert offer.service_id == test_service.id
        assert offer.status == "requested"

    async def test_user_can_create_multiple_appointments_for_same_service(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_two: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response_one = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(hours=1)},
        )
        assert response_one.status_code == status.HTTP_201_CREATED

        response_two = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(hours=5)},
        )
        assert response_two.status_code == status.HTTP_201_CREATED
        assert response_two.json()["id"] != response_one.json()["id"]

    async def test_user_unable_to_create_offer_for_their_own_service_job(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB,
            test_service: ServiceInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_unauthenticated_users_cant_create_appointments(
            self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB,
    ) -> None:
        response = await client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "id, status_code",
        (
                (FAKE_ID, 404),
                (None, 404)
        ),
    )
    async def test_wrong_id_gives_proper_error_status(
            self, app: FastAPI, create_authorized_client: Callable, user_client_three: UserInDB, id: str,
            status_code: int
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_three)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=id),
            json={"start_time": future_time()},
        )

        assert response.status_code == status_code
