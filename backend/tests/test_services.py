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
        category="spot_clean",
    )


@pytest_asyncio.fixture
async def darlenes_services_list(db: Database, user_darlene: UserInDB) -> List[ServiceInDB]:
    service_repo = ServicesRepository(db)

    return [
        await service_repo.create_service(
            new_service=ServiceCreate(
                name=f"test service {i}", description="test description", price=20.00, category="full_clean"
            ),
            requesting_user=user_darlene
        )
        for i in range(5)
    ]


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


class TestCreateservice:
    async def test_valid_input_creates_service(
            self, app: FastAPI, elliots_authorized_client: AsyncClient, new_service: ServiceCreate,
            user_elliot: UserInDB
    ) -> None:
        response = await elliots_authorized_client.post(
            app.url_path_for("services:create-service"), json=new_service.model_dump()
        )

        assert response.status_code == status.HTTP_201_CREATED

        created_service = ServicePublic(**response.json())

        assert created_service.name == new_service.name
        assert created_service.price == new_service.price
        assert created_service.category == new_service.category
        assert created_service.owner == user_elliot.id

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
            elliots_authorized_client: AsyncClient,
            invalid_payload: Dict[str, Union[str, float]],
            test_service: ServiceCreate,
            status_code: int
    ) -> None:
        response = await elliots_authorized_client.post(
            app.url_path_for("services:create-service"),
            json=invalid_payload
        )

        assert response.status_code == status_code


class TestGetservice:
    async def test_get_service_by_id(
            self, app: FastAPI, elliots_authorized_client: AsyncClient, test_service: ServiceInDB
    ) -> None:
        response = await elliots_authorized_client.get(
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
            self, app: FastAPI, elliots_authorized_client: AsyncClient, id: str, status_code: int
    ) -> None:
        response = await elliots_authorized_client.get(app.url_path_for("services:get-service-by-id", service_id=id))

        assert response.status_code == status_code

    async def test_get_all_services_returns_only_user_owned_services(
            self,
            app: FastAPI,
            elliots_authorized_client: AsyncClient,
            user_elliot: UserInDB,
            db: Database,
            test_service: ServiceInDB,
            darlenes_services_list: List[ServiceInDB]
    ) -> None:
        response = await elliots_authorized_client.get(
            app.url_path_for("services:list-all-user-services")
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        services = [ServiceInDB(**l) for l in response.json()]

        print(test_service)

        # TODO: check why this fails
        # assert test_service in services

        for service in services:
            assert service.owner == user_elliot.id

        assert all(c not in services for c in darlenes_services_list)


class TestUpdateservice:
    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
                (["name"], ["new fake service name"]),
                (["description"], ["new fake service description"]),
                (["price"], [3.14]),
                (["category"], ["full_clean"]),
                (
                        ["name", "description"],
                        [
                            "extra new fake service name",
                            "extra new fake service description",
                        ],
                ),
                (["price", "category"], [42.00, "dust_up"]),
        ),
    )
    async def test_update_service_with_valid_input(
            self,
            app: FastAPI,
            elliots_authorized_client: AsyncClient,
            test_service: ServiceInDB,
            attrs_to_change: List[str],
            values: List[str],
    ) -> None:
        service_update = {
            attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))
        }
        res = await elliots_authorized_client.put(
            app.url_path_for(
                "services:update-service-by-id",
                service_id=test_service.id,
            ),
            json=service_update
        )

        assert res.status_code == status.HTTP_200_OK
        updated_service = ServiceInDB(**res.json())
        assert updated_service.id == test_service.id  # make sure it's the same service
        # make sure that any attribute we updated has changed to the correct value
        for i in range(len(attrs_to_change)):
            attr_to_change = getattr(updated_service, attrs_to_change[i])
            assert attr_to_change != getattr(test_service, attrs_to_change[i])
            assert attr_to_change == values[i]
        # make sure that no other attributes' values have changed
        for attr, value in updated_service.model_dump(exclude={"created_at", "updated_at"}).items():
            if attr not in attrs_to_change:
                assert getattr(test_service, attr) == value

    async def test_user_receives_error_if_updating_other_users_services(
            self,
            app: FastAPI,
            # elliot can's modify darlene's service
            elliots_authorized_client: AsyncClient,
            darlenes_services_list: List[ServiceInDB],
    ) -> None:

        response = await elliots_authorized_client.put(
            app.url_path_for(
                "services:update-service-by-id",
                service_id=darlenes_services_list[0].id,
            ),
            json={"price": 99.99}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_cant_change_ownership_of_service(
            self,
            app: FastAPI,
            elliots_authorized_client: AsyncClient,
            test_service: ServiceInDB,
            user_elliot: UserInDB,
            user_darlene: UserInDB
    ) -> None:

        response = await elliots_authorized_client.put(
            app.url_path_for(
                "services:update-service-by-id",
                service_id=test_service.id,
            ),
            json={"owner": user_darlene.id}
        )

        assert response.status_code == status.HTTP_200_OK

        service = ServicePublic(**response.json())

        assert service.owner == user_elliot.id

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
            elliots_authorized_client: AsyncClient,
            id: str,
            payload: dict,
            status_code: int,
            test_service: ServiceInDB
    ) -> None:
        # service_update = {payload}
        res = await elliots_authorized_client.put(
            app.url_path_for("services:update-service-by-id",
                             service_id=id if id is not None else test_service.id),
            json=payload
        )
        assert res.status_code == status_code


class TestDeleteservice:
    async def test_can_delete_service_successfully(
            self,
            app: FastAPI,
            elliots_authorized_client: AsyncClient,
            test_service: ServiceInDB,
    ) -> None:
        # delete the service
        response = await elliots_authorized_client.delete(
            app.url_path_for(
                "services:delete-service-by-id",
                service_id=test_service.id,
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        # ensure that the service no longer exists
        response = await elliots_authorized_client.get(
            app.url_path_for(
                "services:get-service-by-id",
                service_id=test_service.id,
            ),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_user_cant_delete_other_users_service(
            self,
            app: FastAPI,
            elliots_authorized_client: AsyncClient,
            darlenes_services_list: List[ServiceInDB],
    ) -> None:
        # delete the service
        response = await elliots_authorized_client.delete(
            app.url_path_for(
                "services:delete-service-by-id",
                service_id=darlenes_services_list[0].id,
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
            elliots_authorized_client: AsyncClient,
            test_service: ServiceInDB,
            id: str,
            status_code: int,
    ) -> None:
        res = await elliots_authorized_client.delete(
            app.url_path_for(
                "services:delete-service-by-id", service_id=id),
        )
        print(res.json())
        assert res.status_code == status_code
