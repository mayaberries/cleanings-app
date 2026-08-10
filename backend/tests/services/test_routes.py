import uuid

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.services.service import ServiceInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


class TestservicesRoutes:
    @pytest.mark.asyncio
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB) -> None:
        response = await client.post(app.url_path_for("services:create-service"), json={})
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("services:get-service-by-id", service_id=test_service.id))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("services:list-all-user-services"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(app.url_path_for("services:update-service-by-id", service_id=test_service.id))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.delete(app.url_path_for("services:delete-service-by-id", service_id=test_service.id))
        assert response.status_code != status.HTTP_404_NOT_FOUND
