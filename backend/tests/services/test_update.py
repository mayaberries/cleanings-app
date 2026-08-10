import uuid
from typing import List

import pytest
import pytest_asyncio
from databases import Database
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.services import ServicesRepository
from app.models.services.service import ServiceCreate, ServiceInDB, ServicePublic
from app.models.auth.user import UserInDB

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


class TestUpdateService:
    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
                (["name"], ["new fake service name"]),
                (["description"], ["new fake service description"]),
                (["price"], [3.14]),
                (["category"], ["dental_cleaning"]),
                (
                        ["name", "description"],
                        [
                            "extra new fake service name",
                            "extra new fake service description",
                        ],
                ),
                (["price", "category"], [42.00, "vaccination"]),
        ),
    )
    async def test_update_service_with_valid_input(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_service: ServiceInDB,
            attrs_to_change: List[str],
            values: List[str],
    ) -> None:
        service_update = {
            attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))
        }
        res = await clinic_a_admin_client.put(
            app.url_path_for(
                "services:update-service-by-id",
                service_id=test_service.id,
            ),
            json=service_update
        )

        assert res.status_code == status.HTTP_200_OK
        updated_service = ServicePublic(**res.json())

        assert updated_service.id == test_service.id
        for i in range(len(attrs_to_change)):
            attr_to_change = getattr(updated_service, attrs_to_change[i])
            assert attr_to_change != getattr(test_service, attrs_to_change[i])
            assert attr_to_change == values[i]
        test_service_dumped = test_service.model_dump(exclude={"created_at", "updated_at"})
        for attr, value in updated_service.model_dump(exclude={"created_at", "updated_at"}).items():
            if attr not in attrs_to_change:
                assert test_service_dumped[attr] == value

    async def test_user_receives_error_if_updating_other_users_services(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            clinic_b_services_list: List[ServiceInDB],
    ) -> None:

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "services:update-service-by-id",
                service_id=clinic_b_services_list[0].id,
            ),
            json={"price": 99.99}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_cant_change_ownership_of_service(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_service: ServiceInDB,
            user_clinic_a_admin: UserInDB,
            user_clinic_b_admin: UserInDB
    ) -> None:

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "services:update-service-by-id",
                service_id=test_service.id,
            ),
            json={"owner": user_clinic_b_admin.id}
        )

        assert response.status_code == status.HTTP_200_OK

        service = ServicePublic(**response.json())

        assert service.clinic.id == user_clinic_a_admin.clinic_id

    @pytest.mark.parametrize(
        "id, payload, status_code",
        (
                (FAKE_ID, {"name": "test"}, 404),
                (None, None, 422),
                (None, {"category": None}, 400),
        ),
    )
    async def test_update_service_with_invalid_input_throws_error(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            id: str,
            payload: dict,
            status_code: int,
            test_service: ServiceInDB
    ) -> None:
        res = await clinic_a_admin_client.put(
            app.url_path_for("services:update-service-by-id",
                             service_id=id if id is not None else test_service.id),
            json=payload
        )
        assert res.status_code == status_code
