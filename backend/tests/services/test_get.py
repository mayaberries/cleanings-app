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
def new_service():
    return ServiceCreate(
        name="test service",
        description="test description",
        price=0.00,
        category="wellness_exam",
    )


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

class TestGetService:
    async def test_get_service_by_id(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, test_service: ServiceInDB
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("services:get-service-by-id", service_id=test_service.id))
        assert response.status_code == status.HTTP_200_OK
        service = ServicePublic(**response.json()).model_dump(exclude={"owner"})

        assert service == test_service.model_dump(exclude={"owner", "updated_at", "created_at"})

    async def test_unauthorized_users_cant_access_services(
            self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB
    ) -> None:
        response = await client.get(
            app.url_path_for("services:get-service-by-id",
                             service_id=test_service.id)
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "id, status_code",
        (
                (FAKE_ID, 404),
                (None, 404),
        ),
    )
    async def test_wrong_id_returns_error(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, id: str, status_code: int
    ) -> None:
        response = await clinic_a_admin_client.get(app.url_path_for("services:get-service-by-id", service_id=id))

        assert response.status_code == status_code

    async def test_get_all_services_returns_only_user_owned_services(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            user_clinic_a_admin: UserInDB,
            db: Database,
            test_service: ServiceInDB,
            clinic_b_services_list: List[ServiceInDB]
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("services:list-all-user-services")
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        services = [ServiceInDB(**l) for l in response.json()]

        for service in services:
            assert service.owner == user_clinic_a_admin.id

        assert all(c not in services for c in clinic_b_services_list)
