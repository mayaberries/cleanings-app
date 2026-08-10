import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.core.config import PUBLIC_RATE_LIMIT_PER_KEY
from app.models.clinic_api_key import ClinicAPIKeyInDB

pytestmark = pytest.mark.asyncio

"""
Only the per-key limiter is exercised here. The per-IP backstop
(ip_limiter, see app/core/limiter.py) keys off get_remote_address(request),
which depends on request.client being populated with a real socket peer --
that's not guaranteed to behave the same way under httpx's ASGITransport
(no real network involved) as it does behind a real ASGI server, so
asserting on its exact behavior here would risk testing the test
transport's quirks rather than the limiter itself. The per-key limiter
doesn't have this problem since it keys off a header value we control
directly.
"""


class TestPublicKeyRateLimit:
    async def test_per_key_limit_returns_429_once_exceeded(
        self, app: FastAPI, client: AsyncClient, clinic_a_public_key: ClinicAPIKeyInDB
    ) -> None:
        headers = {"X-Clinic-Key": clinic_a_public_key.public_key}
        url = app.url_path_for("public-booking:list-services")

        for _ in range(PUBLIC_RATE_LIMIT_PER_KEY):
            response = await client.get(url, headers=headers)
            assert response.status_code == status.HTTP_200_OK

        blocked = await client.get(url, headers=headers)
        assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    async def test_different_keys_have_independent_budgets(
        self,
        app: FastAPI,
        client: AsyncClient,
        clinic_a_public_key: ClinicAPIKeyInDB,
        clinic_b_public_key: ClinicAPIKeyInDB,
    ) -> None:
        url = app.url_path_for("public-booking:list-services")
        headers_a = {"X-Clinic-Key": clinic_a_public_key.public_key}
        headers_b = {"X-Clinic-Key": clinic_b_public_key.public_key}

        for _ in range(PUBLIC_RATE_LIMIT_PER_KEY):
            response = await client.get(url, headers=headers_a)
            assert response.status_code == status.HTTP_200_OK

        exhausted_a = await client.get(url, headers=headers_a)
        assert exhausted_a.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # clinic B's key hasn't made a single request yet -- separate bucket
        still_fine_b = await client.get(url, headers=headers_b)
        assert still_fine_b.status_code == status.HTTP_200_OK