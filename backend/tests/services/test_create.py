import uuid
from typing import Dict, Union

import pytest
import pytest_asyncio
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.models.service import ServiceCreate, ServicePublic
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


@pytest_asyncio.fixture
def new_service():
    return ServiceCreate(
        name="test service",
        description="test description",
        price=0.00,
        category="wellness_exam",
    )


class TestCreateService:
    async def test_valid_input_creates_service(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, new_service: ServiceCreate,
            user_clinic_a_admin: UserInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("services:create-service"), json=new_service.model_dump()
        )

        assert response.status_code == status.HTTP_201_CREATED

        created_service = ServicePublic(**response.json())

        assert created_service.name == new_service.name
        assert created_service.price == new_service.price
        assert created_service.category == new_service.category
        assert created_service.clinic.id == user_clinic_a_admin.clinic_id
        
    async def test_unauthorized_user_unable_to_create_service(
            self, app: FastAPI, client: AsyncClient, new_service: ServiceCreate
    ) -> None:
        response = await client.post(
            app.url_path_for("services:create-service"),
            json=new_service.model_dump()
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
                (None, 422),
                ({}, 422),
                ({"name": "test"}, 422),
                ({"price": 10.00}, 422),
                ({"name": "test", "description": "test"}, 422),

        )
    )
    async def test_invalid_input_raises_error(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            invalid_payload: Dict[str, Union[str, float]],
            test_service: ServiceCreate,
            status_code: int
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("services:create-service"),
            json=invalid_payload
        )

        assert response.status_code == status_code
