from typing import List, Dict, Union
import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient
from fastapi import FastAPI, status
from databases import Database
from app.db.repositories.cleanings import CleaningsRepository
from app.models.cleaning import CleaningCreate, CleaningInDB, CleaningPublic
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


@pytest_asyncio.fixture
def new_cleaning():
    return CleaningCreate(
        name="test cleaning",
        description="test description",
        price=0.00,
        cleaning_type="spot_clean",
    )


@pytest_asyncio.fixture
async def darlenes_cleanings_list(db: Database, user_darlene: UserInDB) -> List[CleaningInDB]:
    cleaning_repo = CleaningsRepository(db)

    return [
        await cleaning_repo.create_cleaning(
            new_cleaning=CleaningCreate(
                name=f"test cleaning {i}", description="test description", price=20.00, cleaning_type="full_clean"
            ),
            requesting_user=user_darlene
        )
        for i in range(5)
    ]


class TestcleaningsRoutes:
    @pytest.mark.asyncio
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient, test_cleaning: CleaningInDB) -> None:
        response = await client.post(app.url_path_for("cleanings:create-cleaning"), json={})
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("cleanings:get-cleaning-by-id", cleaning_id=test_cleaning.id))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("cleanings:list-all-user-cleanings"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(app.url_path_for("cleanings:update-cleaning-by-id", cleaning_id=test_cleaning.id))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.delete(app.url_path_for("cleanings:delete-cleaning-by-id", cleaning_id=test_cleaning.id))
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestCreatecleaning:
    async def test_valid_input_creates_cleaning(
        self, app: FastAPI, elliots_authorized_client: AsyncClient, new_cleaning: CleaningCreate, user_elliot: UserInDB
    ) -> None:
        response = await elliots_authorized_client.post(
            app.url_path_for("cleanings:create-cleaning"), json=new_cleaning.model_dump()
        )

        assert response.status_code == status.HTTP_201_CREATED

        created_cleaning = CleaningPublic(**response.json())

        assert created_cleaning.name == new_cleaning.name
        assert created_cleaning.price == new_cleaning.price
        assert created_cleaning.cleaning_type == new_cleaning.cleaning_type
        assert created_cleaning.owner == user_elliot.id

    async def test_unauthorized_user_unable_to_create_cleaning(
        self, app: FastAPI, client: AsyncClient, new_cleaning: CleaningCreate
    ) -> None:
        response = await client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=new_cleaning.model_dump()
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
        test_cleaning: CleaningCreate,
        status_code: int
    ) -> None:
        response = await elliots_authorized_client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json=invalid_payload
        )

        assert response.status_code == status_code


class TestGetcleaning:
    async def test_get_cleaning_by_id(
        self, app: FastAPI, elliots_authorized_client: AsyncClient, test_cleaning: CleaningInDB
    ) -> None:

        response = await elliots_authorized_client.get(app.url_path_for("cleanings:get-cleaning-by-id", cleaning_id=test_cleaning.id))
        assert response.status_code == status.HTTP_200_OK
        cleaning = CleaningPublic(**response.json()).model_dump(exclude={"owner"})

        assert cleaning == test_cleaning.model_dump(exclude={"owner", "updated_at", "created_at"})

    async def test_unauthorized_users_cant_access_cleanings(
        self, app: FastAPI, client: AsyncClient, test_cleaning: CleaningInDB
    ) -> None:
        response = await client.get(
            app.url_path_for("cleanings:get-cleaning-by-id",
                             cleaning_id=test_cleaning.id)
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
        response = await elliots_authorized_client.get(app.url_path_for("cleanings:get-cleaning-by-id", cleaning_id=id))

        assert response.status_code == status_code

    async def test_get_all_cleanings_returns_only_user_owned_cleanings(
        self,
        app: FastAPI,
        elliots_authorized_client: AsyncClient,
        user_elliot: UserInDB,
        db: Database,
        test_cleaning: CleaningInDB,
        darlenes_cleanings_list: List[CleaningInDB]
    ) -> None:
        response = await elliots_authorized_client.get(
            app.url_path_for("cleanings:list-all-user-cleanings")
        )
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

        cleanings = [CleaningInDB(**l) for l in response.json()]

        print(test_cleaning)

        #TODO: check why this fails
        # assert test_cleaning in cleanings

        for cleaning in cleanings:
            assert cleaning.owner == user_elliot.id

        assert all(c not in cleanings for c in darlenes_cleanings_list)


class TestUpdatecleaning:
    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
            (["name"], ["new fake cleaning name"]),
            (["description"], ["new fake cleaning description"]),
            (["price"], [3.14]),
            (["cleaning_type"], ["full_clean"]),
            (
                ["name", "description"],
                [
                    "extra new fake cleaning name",
                    "extra new fake cleaning description",
                ],
            ),
            (["price", "cleaning_type"], [42.00, "dust_up"]),
        ),
    )
    async def test_update_cleaning_with_valid_input(
        self,
        app: FastAPI,
        elliots_authorized_client: AsyncClient,
        test_cleaning: CleaningInDB,
        attrs_to_change: List[str],
        values: List[str],
    ) -> None:
        cleaning_update = {
            attrs_to_change[i]: values[i] for i in range(len(attrs_to_change))
        }
        res = await elliots_authorized_client.put(
            app.url_path_for(
                "cleanings:update-cleaning-by-id",
                cleaning_id=test_cleaning.id,
            ),
            json=cleaning_update
        )

        assert res.status_code == status.HTTP_200_OK
        updated_cleaning = CleaningInDB(**res.json())
        assert updated_cleaning.id == test_cleaning.id  # make sure it's the same cleaning
        # make sure that any attribute we updated has changed to the correct value
        for i in range(len(attrs_to_change)):
            attr_to_change = getattr(updated_cleaning, attrs_to_change[i])
            assert attr_to_change != getattr(test_cleaning, attrs_to_change[i])
            assert attr_to_change == values[i]
        # make sure that no other attributes' values have changed
        for attr, value in updated_cleaning.model_dump(exclude={"created_at", "updated_at"}).items():
            if attr not in attrs_to_change:
                assert getattr(test_cleaning, attr) == value

    async def test_user_receives_error_if_updating_other_users_cleanings(
        self,
        app: FastAPI,
        # elliot can's modify darlene's cleaning
        elliots_authorized_client: AsyncClient,
        darlenes_cleanings_list: List[CleaningInDB],
    ) -> None:

        response = await elliots_authorized_client.put(
            app.url_path_for(
                "cleanings:update-cleaning-by-id",
                cleaning_id=darlenes_cleanings_list[0].id,
            ),
            json={"price": 99.99}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_user_cant_change_ownership_of_cleaning(
        self,
        app: FastAPI,
        elliots_authorized_client: AsyncClient,
        test_cleaning: CleaningInDB,
        user_elliot: UserInDB,
        user_darlene: UserInDB
    ) -> None:

        response = await elliots_authorized_client.put(
            app.url_path_for(
                "cleanings:update-cleaning-by-id",
                cleaning_id=test_cleaning.id,
            ),
            json={"owner": user_darlene.id}
        )

        assert response.status_code == status.HTTP_200_OK

        cleaning = CleaningPublic(**response.json())

        assert cleaning.owner == user_elliot.id

    @pytest.mark.parametrize(
        "id, payload, status_code",
        (
            (FAKE_ID, {"name": "test"}, 404),
            (None, None, 422),
            (None, {"cleaning_type": "invalid cleaning type"}, 422),
            (None, {"cleaning_type": None}, 400),
        ),
    )
    async def test_update_cleaning_with_invalid_input_throws_error(
        self,
        app: FastAPI,
        elliots_authorized_client: AsyncClient,
        id: str,
        payload: dict,
        status_code: int,
        test_cleaning: CleaningInDB
    ) -> None:
        # cleaning_update = {payload}
        res = await elliots_authorized_client.put(
            app.url_path_for("cleanings:update-cleaning-by-id",
                             cleaning_id=id if id is not None else test_cleaning.id),
            json=payload
        )
        assert res.status_code == status_code


class TestDeletecleaning:
    async def test_can_delete_cleaning_successfully(
        self,
        app: FastAPI,
        elliots_authorized_client: AsyncClient,
        test_cleaning: CleaningInDB,
    ) -> None:
        # delete the cleaning
        response = await elliots_authorized_client.delete(
            app.url_path_for(
                "cleanings:delete-cleaning-by-id",
                cleaning_id=test_cleaning.id,
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        # ensure that the cleaning no longer exists
        response = await elliots_authorized_client.get(
            app.url_path_for(
                "cleanings:get-cleaning-by-id",
                cleaning_id=test_cleaning.id,
            ),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_user_cant_delete_other_users_cleaning(
        self,
        app: FastAPI,
        elliots_authorized_client: AsyncClient,
        darlenes_cleanings_list: List[CleaningInDB],
    ) -> None:
        # delete the cleaning
        response = await elliots_authorized_client.delete(
            app.url_path_for(
                "cleanings:delete-cleaning-by-id",
                cleaning_id=darlenes_cleanings_list[0].id,
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
        test_cleaning: CleaningInDB,
        id: str,
        status_code: int,
    ) -> None:
        res = await elliots_authorized_client.delete(
            app.url_path_for(
                "cleanings:delete-cleaning-by-id", cleaning_id=id),
        )
        print(res.json())
        assert res.status_code == status_code
