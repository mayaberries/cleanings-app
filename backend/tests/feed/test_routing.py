import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestFeedRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.get(
            app.url_path_for("feed:get-service-feed-for-user")
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND
