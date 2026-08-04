import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import (
    HTTP_404_NOT_FOUND,
)

pytestmark = pytest.mark.asyncio


class TestUserRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        new_user = {
            "email": "test@email.io",
            "username": "testname",
            "password": "password123"
        }

        response = await client.post(app.url_path_for("users:register-new-user"), json=new_user)

        assert response.status_code != HTTP_404_NOT_FOUND
