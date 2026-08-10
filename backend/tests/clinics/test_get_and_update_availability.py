import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient
from databases import Database

from app.db.repositories.clinic_availability import ClinicAvailabilityRepository
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestGetClinicAvailability:
    async def test_new_clinic_is_provisioned_with_default_hours_at_creation(
        self, db: Database, user_clinic_a_admin: UserInDB
    ) -> None:
        # Checks the eager path (create_clinic_for_admin), not just the
        # get_or_create fallback -- a row should exist without ever
        # calling GET.
        availability_repo = ClinicAvailabilityRepository(db)
        availability = await availability_repo.get_availability_by_clinic_id(
            clinic_id=user_clinic_a_admin.clinic_id
        )
        assert availability is not None
        assert availability.schedule["monday"][0].start.isoformat() == "09:00:00"
        assert availability.schedule["saturday"] == []

    async def test_get_availability_requires_no_auth(
        self, app: FastAPI, client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        # Mirrors GET /clinics/{clinic_id}/'s existing (lack of) permission
        # check -- see dependencies/clinics.py.
        response = await client.get(
            app.url_path_for("clinic-availability:get-availability", clinic_id=user_clinic_a_admin.clinic_id)
        )
        assert response.status_code == status.HTTP_200_OK


class TestUpdateClinicAvailability:
    async def test_admin_can_update_own_clinic_hours(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        payload = {
            "schedule": {
                "monday": [{"start": "10:00:00", "end": "14:00:00"}],
                "friday": [{"start": "08:00:00", "end": "12:00:00"}, {"start": "13:00:00", "end": "18:00:00"}],
            },
            "timezone": "America/Mexico_City",
        }
        response = await clinic_a_admin_client.put(
            app.url_path_for("clinic-availability:update-availability", clinic_id=user_clinic_a_admin.clinic_id),
            json=payload,
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["timezone"] == "America/Mexico_City"
        assert body["schedule"]["monday"] == [{"start": "10:00:00", "end": "14:00:00"}]
        # days omitted from the payload are normalized to closed, not left
        # as whatever the default/previous value was
        assert body["schedule"]["tuesday"] == []

    async def test_overlapping_ranges_rejected(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        payload = {
            "schedule": {
                "monday": [
                    {"start": "09:00:00", "end": "13:00:00"},
                    {"start": "12:00:00", "end": "17:00:00"},
                ]
            }
        }
        response = await clinic_a_admin_client.put(
            app.url_path_for("clinic-availability:update-availability", clinic_id=user_clinic_a_admin.clinic_id),
            json=payload,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_end_before_start_rejected(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        payload = {"schedule": {"monday": [{"start": "17:00:00", "end": "09:00:00"}]}}
        response = await clinic_a_admin_client.put(
            app.url_path_for("clinic-availability:update-availability", clinic_id=user_clinic_a_admin.clinic_id),
            json=payload,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_clinic_aux_cannot_update_hours(
        self, app: FastAPI, create_authorized_client, user_clinic_a_aux: UserInDB
    ) -> None:
        aux_client = create_authorized_client(user=user_clinic_a_aux)
        response = await aux_client.put(
            app.url_path_for("clinic-availability:update-availability", clinic_id=user_clinic_a_aux.clinic_id),
            json={"schedule": {}},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_admin_cannot_update_other_clinics_hours(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_b_admin: UserInDB
    ) -> None:
        response = await clinic_a_admin_client.put(
            app.url_path_for("clinic-availability:update-availability", clinic_id=user_clinic_b_admin.clinic_id),
            json={"schedule": {}},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN