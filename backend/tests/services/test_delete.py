from typing import List, Dict, Union
import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from fastapi import FastAPI, status
from databases import Database
from app.db.repositories.services import ServicesRepository
from app.models.service import ServiceCreate, ServiceInDB, ServicePublic
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


@pytest_asyncio.fixture
async def clinic_b_services_list(db: Database, user_clinic_b_admin: UserInDB) -> List[ServiceInDB]:
    service_repo = ServicesRepository(db)

    return [
        await service_repo.create_service(
            new_service=ServiceCreate(
                name=f"test service {i}", description="test description", price=20.00, category="vaccination"
            ),
            requesting_user=user_clinic_b_admin
        )
        for i in range(5)
    ]


class TestDeleteService:
    async def test_can_delete_service_successfully(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_service: ServiceInDB,
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for(
                "services:delete-service-by-id",
                service_id=test_service.id,
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        response = await clinic_a_admin_client.get(
            app.url_path_for(
                "services:get-service-by-id",
                service_id=test_service.id,
            ),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_user_cant_delete_other_users_service(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_b_services_list: List[ServiceInDB],
    ) -> None:
        response = await clinic_a_admin_client.delete(
            app.url_path_for(
                "services:delete-service-by-id",
                service_id=clinic_b_services_list[0].id,
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize(
        "id, status_code",
        (
                (FAKE_ID, 404),
                (None, 404),
        ),
    )
    async def test_wrong_id_throws_error(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_service: ServiceInDB,
            id: str,
            status_code: int,
    ) -> None:
        res = await clinic_a_admin_client.delete(
            app.url_path_for(
                "services:delete-service-by-id", service_id=id),
        )
        assert res.status_code == status_code
