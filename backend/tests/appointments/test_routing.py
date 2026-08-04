import datetime
import uuid

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


class TestAppointmentRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.post(app.url_path_for("appointments:create-appointment", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("appointments:list-appointments-for-service", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(
            app.url_path_for("appointments:get-appointment-by-id", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(
            app.url_path_for("appointments:confirm-appointment", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(
            app.url_path_for("appointments:cancel-appointment", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.delete(
            app.url_path_for("appointments:withdraw-appointment", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND
