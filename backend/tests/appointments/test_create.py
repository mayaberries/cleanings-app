import datetime
import uuid
from typing import Callable

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.appointments.appointment import AppointmentPublic
from app.models.profiles.pet_profile import PetProfileInDB
from app.models.services.service import ServiceInDB
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


def future_time(hours: int = 1) -> str:
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).isoformat()


class TestCreateAppointments:
    async def test_user_can_successfully_create_offer_for_other_users_service_job(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_one: UserInDB, user_client_one_pet: PetProfileInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(), "pet_id": user_client_one_pet.id},
        )
        assert response.status_code == status.HTTP_201_CREATED

        offer = AppointmentPublic(**response.json())
        assert offer.user_id == user_client_one.id
        assert offer.pet_id == user_client_one_pet.id
        assert offer.service_id == test_service.id
        assert offer.status == "requested"

    async def test_user_can_create_multiple_appointments_for_same_service(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_two: UserInDB, user_client_two_pet: PetProfileInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response_one = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(hours=1), "pet_id": user_client_two_pet.id},
        )
        assert response_one.status_code == status.HTTP_201_CREATED

        response_two = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(hours=5), "pet_id": user_client_two_pet.id},
        )
        assert response_two.status_code == status.HTTP_201_CREATED
        assert response_two.json()["id"] != response_one.json()["id"]

    async def test_user_unable_to_create_offer_for_their_own_service_job(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB,
            test_service: ServiceInDB
    ) -> None:
        # Fails on the service-ownership check before the pet is ever
        # looked up, so a syntactically-valid but nonexistent pet_id is
        # fine here -- exercising that ordering is the point.
        response = await clinic_a_admin_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(), "pet_id": FAKE_ID},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_unauthenticated_users_cant_create_appointments(
            self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB,
    ) -> None:
        response = await client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(), "pet_id": FAKE_ID},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_cannot_create_appointment_for_another_owners_pet(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_one: UserInDB, user_client_two_pet: PetProfileInDB,
    ) -> None:
        # user_client_one tries to book against user_client_two's pet.
        authorized_client = create_authorized_client(user=user_client_one)
        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(), "pet_id": user_client_two_pet.id},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_missing_pet_id_rejected(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_one: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)
        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "id, status_code",
        ((FAKE_ID, 404), (None, 404)),
    )
    async def test_wrong_id_gives_proper_error_status(
            self, app: FastAPI, create_authorized_client: Callable, user_client_three: UserInDB,
            user_client_three_pet: PetProfileInDB, id: str, status_code: int
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_three)
        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=id),
            json={"start_time": future_time(), "pet_id": user_client_three_pet.id},
        )
        assert response.status_code == status_code
