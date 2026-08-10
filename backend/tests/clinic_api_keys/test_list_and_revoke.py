import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.clinic_api_key import ClinicAPIKeyInDB

pytestmark = pytest.mark.asyncio


class TestListClinicAPIKeys:
    async def test_admin_can_list_own_keys(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, clinic_a_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("clinic-api-keys:list-keys", clinic_id=clinic_a_public_key.clinic_id)
        )
        assert response.status_code == status.HTTP_200_OK
        keys = response.json()
        assert any(k["id"] == clinic_a_public_key.id for k in keys)
        # the value is fully returned, not masked -- it's a publishable
        # key, not a secret, see ClinicAPIKeyPublic's docstring
        assert any(k["public_key"] == clinic_a_public_key.public_key for k in keys)

    async def test_admin_cannot_list_other_clinics_keys(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, clinic_b_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("clinic-api-keys:list-keys", clinic_id=clinic_b_public_key.clinic_id)
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRevokeClinicAPIKey:
    async def test_admin_can_revoke_own_key(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, clinic_a_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for(
                "clinic-api-keys:revoke-key",
                clinic_id=clinic_a_public_key.clinic_id,
                key_id=clinic_a_public_key.id,
            )
        )
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["is_active"] is False
        assert body["revoked_at"] is not None

    async def test_revoked_key_can_no_longer_authenticate_public_routes(
        self,
        app: FastAPI,
        clinic_a_admin_client: AsyncClient,
        client: AsyncClient,
        clinic_a_public_key: ClinicAPIKeyInDB,
    ) -> None:
        await clinic_a_admin_client.delete(
            app.url_path_for(
                "clinic-api-keys:revoke-key",
                clinic_id=clinic_a_public_key.clinic_id,
                key_id=clinic_a_public_key.id,
            )
        )
        response = await client.get(
            app.url_path_for("public-booking:list-services"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_admin_cannot_revoke_other_clinics_key(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, clinic_b_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for(
                "clinic-api-keys:revoke-key",
                clinic_id=clinic_b_public_key.clinic_id,
                key_id=clinic_b_public_key.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_revoking_unknown_key_id_returns_404(
        self, app: FastAPI, clinic_a_admin_client: AsyncClient, clinic_a_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for(
                "clinic-api-keys:revoke-key",
                clinic_id=clinic_a_public_key.clinic_id,
                key_id="00000000-0000-0000-0000-000000000000",
            )
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND