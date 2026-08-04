import uuid

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())

class TestEvaluationRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.post(
            app.url_path_for(
                "evaluations:create-evaluation-for-appointment", service_id=FAKE_ID, appointment_id=FAKE_ID
            )
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(
            app.url_path_for(
                "evaluations:get-evaluation-for-appointment", service_id=FAKE_ID, appointment_id=FAKE_ID
            )
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("evaluations:list-evaluations-for-cleaner", username="bradpitt"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("evaluations:get-stats-for-cleaner", username="bradpitt"))
        assert response.status_code != status.HTTP_404_NOT_FOUND
