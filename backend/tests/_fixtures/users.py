from typing import List

import pytest_asyncio
from databases import Database
from httpx import AsyncClient

from app.core.config import SECRET_KEY, JWT_TOKEN_PREFIX
from app.db.repositories.users import UsersRepository
from app.models.user import UserCreate, UserInDB, UserRole
from app.services import auth_service


async def user_fixture_helper(
        *, db: Database, new_user: UserCreate, role: UserRole = UserRole.client
) -> UserInDB:
    user_repo = UsersRepository(db)

    existing_user = await user_repo.get_user_by_email(email=new_user.email)

    if existing_user:
        return existing_user

    return await user_repo.register_new_user(new_user=new_user, role=role)


@pytest_asyncio.fixture
def create_authorized_client(client: AsyncClient):
    """
    Generic factory: create_authorized_client(user=some_user) -> AsyncClient
    Prefer this over the named single-user fixtures below for new tests.
    """

    def _create_authorized_client(*, user: UserInDB) -> AsyncClient:
        access_token = auth_service.create_access_token_for_user(
            user=user, secret_key=str(SECRET_KEY))

        client.headers = {
            **client.headers,
            "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}"
        }

        return client

    return _create_authorized_client


@pytest_asyncio.fixture
async def user_clinic_a_admin(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="admin@clinic-a.io",
        username="clinic_a_admin",
        password="clinicAadmin123"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.clinic_admin)


@pytest_asyncio.fixture
async def user_clinic_a_aux(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="aux@clinic-a.io",
        username="clinic_a_aux",
        password="clinicAaux123"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.clinic_aux)


@pytest_asyncio.fixture
async def user_clinic_b_admin(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="admin@clinic-b.io",
        username="clinic_b_admin",
        password="clinicBadmin123"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.clinic_admin)


@pytest_asyncio.fixture
async def user_clinic_b_aux(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="aux@clinic-b.io",
        username="clinic_b_aux",
        password="clinicBaux123"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.clinic_aux)


@pytest_asyncio.fixture
async def user_client_one(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="client-one@sample.io",
        username="client_one",
        password="clientOnePass"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.client)


@pytest_asyncio.fixture
async def user_client_two(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="client-two@sample.io",
        username="client_two",
        password="clientTwoPass"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.client)


@pytest_asyncio.fixture
async def user_client_three(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="client-three@sample.io",
        username="client_three",
        password="clientThreePass"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.client)


@pytest_asyncio.fixture
async def user_client_four(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="client-four@sample.io",
        username="client_four",
        password="clientFourPass"
    )
    return await user_fixture_helper(db=db, new_user=new_user, role=UserRole.client)


@pytest_asyncio.fixture
async def clinic_a_staff(
        user_clinic_a_admin: UserInDB, user_clinic_a_aux: UserInDB
) -> List[UserInDB]:
    return [user_clinic_a_admin, user_clinic_a_aux]


@pytest_asyncio.fixture
async def clinic_b_staff(
        user_clinic_b_admin: UserInDB, user_clinic_b_aux: UserInDB
) -> List[UserInDB]:
    return [user_clinic_b_admin, user_clinic_b_aux]


@pytest_asyncio.fixture
async def test_client_list(
        user_client_one: UserInDB,
        user_client_two: UserInDB,
        user_client_three: UserInDB,
        user_client_four: UserInDB,
) -> List[UserInDB]:
    return [user_client_one, user_client_two, user_client_three, user_client_four]


@pytest_asyncio.fixture
def clinic_a_admin_client(create_authorized_client, user_clinic_a_admin: UserInDB) -> AsyncClient:
    return create_authorized_client(user=user_clinic_a_admin)


@pytest_asyncio.fixture
def clinic_b_admin_client(create_authorized_client, user_clinic_b_admin: UserInDB) -> AsyncClient:
    return create_authorized_client(user=user_clinic_b_admin)
