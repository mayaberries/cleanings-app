import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestProfileRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient, user_client_one: UserInDB) -> None:
        response = await client.get(
            app.url_path_for("profiles:get-profile-by-username", username=user_client_one.username))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(app.url_path_for("profiles:update-own-profile"), json={})
        assert response.status_code != status.HTTP_404_NOT_FOUND
