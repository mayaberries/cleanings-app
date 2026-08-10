import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.clinics.clinic_api_key import ClinicAPIKeyInDB

pytestmark = pytest.mark.asyncio


class TestPublicKeyAuth:
    async def test_missing_key_header_rejected(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.get(app.url_path_for("public-booking:list-services"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_malformed_key_rejected(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.get(
            app.url_path_for("public-booking:list-services"),
            headers={"X-Clinic-Key": "not-a-real-key"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_unknown_but_well_formed_key_rejected(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.get(
            app.url_path_for("public-booking:list-services"),
            headers={"X-Clinic-Key": "pk_live_doesnotexist00000000000000000000000"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_valid_key_is_accepted(
        self, app: FastAPI, client: AsyncClient, clinic_a_public_key: ClinicAPIKeyInDB
    ) -> None:
        response = await client.get(
            app.url_path_for("public-booking:list-services"),
            headers={"X-Clinic-Key": clinic_a_public_key.public_key},
        )
        assert response.status_code == status.HTTP_200_OK

    async def test_jwt_is_not_accepted_as_a_clinic_key(self, app: FastAPI, client: AsyncClient) -> None:
        # The two auth stacks share no code path -- a JWT bearer token
        # doesn't even pass the pk_live_/pk_test_ prefix check.
        response = await client.get(
            app.url_path_for("public-booking:list-services"),
            headers={"X-Clinic-Key": "eyJhbGciOiJIUzI1NiJ9.fake.jwt"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED