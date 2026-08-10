import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestCreateClinicAPIKey:
    async def test_admin_can_create_key_for_own_clinic(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={"label": "Main website widget"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        body = response.json()
        assert body["public_key"].startswith("pk_live_")
        assert body["label"] == "Main website widget"
        assert body["is_active"] is True
        assert body["clinic_id"] == user_clinic_a_admin.clinic_id

    async def test_key_defaults_to_live_environment(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["environment"] == "live"

    async def test_test_environment_key_has_correct_prefix(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={"environment": "test"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["public_key"].startswith("pk_test_")

    async def test_admin_cannot_create_key_for_other_clinic(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_b_admin: UserInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_b_admin.clinic_id),
            json={"label": "sneaky"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_clinic_aux_cannot_create_key(
        self,
        app: FastAPI,
        create_authorized_client,
        user_clinic_a_aux: UserInDB,
        user_clinic_a_admin: UserInDB,
    ) -> None:
        aux_client = create_authorized_client(user=user_clinic_a_aux)
        response = await aux_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={"label": "aux trying"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_unauthenticated_request_rejected(
        self, app: FastAPI, client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        response = await client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={"label": "no auth"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_two_keys_can_coexist_for_same_clinic(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        first = await clinic_a_admin_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={"label": "first"},
        )
        second = await clinic_a_admin_client.post(
            app.url_path_for("clinic-api-keys:create-key", clinic_id=user_clinic_a_admin.clinic_id),
            json={"label": "second"},
        )
        assert first.status_code == second.status_code == status.HTTP_201_CREATED
        assert first.json()["public_key"] != second.json()["public_key"]