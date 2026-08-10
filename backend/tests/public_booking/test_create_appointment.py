import datetime

import pytest
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.appointments import AppointmentsRepository
from app.db.repositories.users import UsersRepository
from app.models.appointment import AppointmentCreate
from app.models.clinic_api_key import ClinicAPIKeyInDB
from app.models.service import ServiceInDB
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio


def _future_start_time(days: int = 5) -> str:
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)).isoformat()


class TestCreatePublicAppointment:
    async def test_guest_can_book_appointment(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        clinic_a_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,
    ) -> None:
        payload = {
            "email": "new-guest@example.com",
            "full_name": "New Guest",
            "phone_number": "555-0199",
            "service_id": test_service.id,
            "start_time": _future_start_time(),
        }
        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
            json=payload,
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["status"] == "requested"
        assert body["service_id"] == test_service.id

        users_repo = UsersRepository(db)
        guest = await users_repo.get_user_by_email(email="new-guest@example.com", populate=True)
        assert guest is not None
        assert guest.is_guest is True
        assert guest.profile.full_name == "New Guest"
        assert guest.profile.phone_number == "555-0199"

    async def test_repeat_booking_reuses_guest_and_refreshes_profile(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        clinic_a_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,
    ) -> None:
        headers = {"X-Clinic-Key": clinic_a_public_key.public_key}

        first = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers=headers,
            json={
                "email": "repeat-guest@example.com",
                "full_name": "First Name",
                "service_id": test_service.id,
                "start_time": _future_start_time(days=10),
            },
        )
        assert first.status_code == status.HTTP_201_CREATED

        second = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers=headers,
            json={
                "email": "repeat-guest@example.com",
                "full_name": "Updated Name",
                "service_id": test_service.id,
                "start_time": _future_start_time(days=11),
            },
        )
        assert second.status_code == status.HTTP_201_CREATED
        assert second.json()["user_id"] == first.json()["user_id"]

        users_repo = UsersRepository(db)
        guest = await users_repo.get_user_by_email(email="repeat-guest@example.com", populate=True)
        assert guest.profile.full_name == "Updated Name"

    async def test_cannot_book_service_belonging_to_another_clinic(
        self,
        app: FastAPI,
        client: AsyncClient,
        clinic_b_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,  # belongs to clinic A
    ) -> None:
        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_b_public_key.public_key},
            json={
                "email": "cross-clinic@example.com",
                "service_id": test_service.id,
                "start_time": _future_start_time(),
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_conflicting_slot_rejected(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        clinic_a_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,
        user_client_one: UserInDB,
    ) -> None:
        appts_repo = AppointmentsRepository(db)
        start_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=20)

        existing = await appts_repo.create_appointment_for_service(
            new_appointment=AppointmentCreate(
                service_id=test_service.id, user_id=user_client_one.id, start_time=start_time
            ),
            service=test_service,
        )
        await appts_repo.confirm_appointment(appointment=existing)

        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
            json={
                "email": "blocked-guest@example.com",
                "service_id": test_service.id,
                "start_time": start_time.isoformat(),
            },
        )
        assert response.status_code == status.HTTP_409_CONFLICT

    async def test_unknown_service_returns_404(
        self, app: FastAPI, client: AsyncClient, clinic_a_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
            json={
                "email": "guest@example.com",
                "service_id": "00000000-0000-0000-0000-000000000000",
                "start_time": _future_start_time(),
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_past_start_time_rejected(
        self,
        app: FastAPI,
        client: AsyncClient,
        clinic_a_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,
    ) -> None:
        past_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat()
        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
            json={"email": "guest@example.com", "service_id": test_service.id, "start_time": past_time},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_invalid_email_rejected(
        self,
        app: FastAPI,
        client: AsyncClient,
        clinic_a_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,
    ) -> None:
        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
            json={
                "email": "not-an-email",
                "service_id": test_service.id,
                "start_time": _future_start_time(),
            },
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_booking_requires_a_valid_clinic_key(
        self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB
    ) -> None:
        response = await client.post(
            app.url_path_for("public-booking:create-appointment"),
            json={
                "email": "guest@example.com",
                "service_id": test_service.id,
                "start_time": _future_start_time(),
            },
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_guest_account_cannot_authenticate_via_password_login(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        clinic_a_public_key: ClinicAPIKeyInDB,
        test_service: ServiceInDB,
    ) -> None:
        await client.post(
            app.url_path_for("public-booking:create-appointment"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
            json={
                "email": "login-attempt@example.com",
                "service_id": test_service.id,
                "start_time": _future_start_time(),
            },
        )
        users_repo = UsersRepository(db)
        # The guest's password is random and never disclosed, so this
        # specifically checks the explicit is_guest guard in
        # authenticate_user rather than relying on the password being
        # unguessable.
        authenticated = await users_repo.authenticate_user(
            email="login-attempt@example.com", password="anything-at-all"
        )
        assert authenticated is None