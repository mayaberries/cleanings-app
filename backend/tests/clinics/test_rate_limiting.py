import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.core.config import CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestClinicAvailabilityRateLimit:
    async def test_per_clinic_limit_returns_429_once_exceeded(
        self, app: FastAPI, client: AsyncClient, user_clinic_a_admin: UserInDB
    ) -> None:
        url = app.url_path_for("clinic-availability:get-availability", clinic_id=user_clinic_a_admin.clinic_id)

        for _ in range(CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC):
            response = await client.get(url)
            assert response.status_code == status.HTTP_200_OK

        blocked = await client.get(url)
        assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    async def test_different_clinics_have_independent_budgets(
        self, app: FastAPI, client: AsyncClient, user_clinic_a_admin: UserInDB, user_clinic_b_admin: UserInDB
    ) -> None:
        url_a = app.url_path_for("clinic-availability:get-availability", clinic_id=user_clinic_a_admin.clinic_id)
        url_b = app.url_path_for("clinic-availability:get-availability", clinic_id=user_clinic_b_admin.clinic_id)

        for _ in range(CLINIC_AVAILABILITY_RATE_LIMIT_PER_CLINIC):
            assert (await client.get(url_a)).status_code == status.HTTP_200_OK

        assert (await client.get(url_a)).status_code == status.HTTP_429_TOO_MANY_REQUESTS
        # clinic B hasn't made a request yet -- independent bucket
        assert (await client.get(url_b)).status_code == status.HTTP_200_OK