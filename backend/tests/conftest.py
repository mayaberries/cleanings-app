from typing import Callable, List, Any, AsyncGenerator
import random
import warnings
import os
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from databases import Database
import alembic
from alembic.config import Config

from app.models.service import ServiceCreate, ServiceInDB, ServiceUpdate
from app.db.repositories.services import ServicesRepository

from app.models.user import UserCreate, UserInDB
from app.db.repositories.users import UsersRepository

from app.core.config import SECRET_KEY, JWT_TOKEN_PREFIX
from app.services import auth_service

from app.models.offer import OfferCreate
from app.db.repositories.offers import OffersRepository


from app.models.evaluation import EvaluationCreate
from app.db.repositories.evaluations import EvaluationsRepository

# Apply migrations at beginning and end of testing session

@pytest_asyncio.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")
# Create a new application for testing


@pytest_asyncio.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application
    return get_application()
# Grab a reference to our database when needed


@pytest_asyncio.fixture
def db(app: FastAPI) -> Database:
    return app.state._db
# Make requests in our tests



@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, Any]:
    async with LifespanManager(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
            headers={"Content-Type": "application/json"}
        ) as client:
            yield client

@pytest_asyncio.fixture
async def test_service(db: Database, user_elliot: UserInDB) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    new_service = ServiceCreate(
        name="fake service name",
        description="fake service description",
        price=9.99,
        category="spot_clean",
    )
    return await service_repo.create_service(new_service=new_service, requesting_user=user_elliot)


async def user_fixture_helper(*, db: Database, new_user: UserCreate) -> UserInDB:
    user_repo = UsersRepository(db)

    existing_user = await user_repo.get_user_by_email(email=new_user.email)

    if existing_user:
        return existing_user

    return await user_repo.register_new_user(new_user=new_user)


@pytest_asyncio.fixture
def elliots_authorized_client(client: AsyncClient, user_elliot: UserInDB) -> AsyncClient:
    access_token = auth_service.create_access_token_for_user(
        user=user_elliot, secret_key=str(SECRET_KEY))

    client.headers = {
        **client.headers,
        "Authorization": f"{JWT_TOKEN_PREFIX} {access_token}"
    }

    return client


@pytest_asyncio.fixture
async def user_elliot(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="elliot@sample.io",
        username="elliot",
        password="evenflow"
    )

    return await user_fixture_helper(db=db, new_user=new_user)


@pytest_asyncio.fixture
async def user_darlene(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="darlene@sample.com",
        username="darlene",
        password="ones-and-zer0es.mpeg"
    )

    return await user_fixture_helper(db=db, new_user=new_user)


@pytest_asyncio.fixture
async def user_mr_robot(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="mr@robot.com",
        username="mrRobot",
        password="d3bug.mkv"
    )

    return await user_fixture_helper(db=db, new_user=new_user)


@pytest_asyncio.fixture
async def user_tyrell(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="tyrell@wellick.com",
        username="tyrell",
        password="bonsoir_elliot"
    )

    return await user_fixture_helper(db=db, new_user=new_user)


@pytest_asyncio.fixture
async def user_angela(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="angela@sample.com",
        username="angela",
        password="everybodywantstoruletheworld"
    )

    return await user_fixture_helper(db=db, new_user=new_user)


@pytest_asyncio.fixture
async def user_trenton(db: Database) -> UserInDB:
    new_user = UserCreate(
        email="trenton@sample.com",
        username="trenton",
        password="3xpl0its.wmv"
    )

    return await user_fixture_helper(db=db, new_user=new_user)


@pytest_asyncio.fixture
async def test_user_list(
    user_mr_robot: UserInDB, user_tyrell: UserInDB, user_angela: UserInDB, user_trenton: UserInDB,
) -> List[UserInDB]:
    return [user_mr_robot, user_tyrell, user_angela, user_trenton]


@pytest_asyncio.fixture
def create_authorized_client(client: AsyncClient) -> Callable:
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
async def test_service_with_offers(
    db: Database,
    user_darlene: UserInDB,
    test_user_list: List[UserInDB]
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    offers_repo = OffersRepository(db)

    new_service = ServiceCreate(
        name="service with offers", description="lorem ipsum", price=9.99, category="full_clean"
    )

    created_service = await service_repo.create_service(
        new_service=new_service, requesting_user=user_darlene
    )

    for user in test_user_list:
        if user.id != user_darlene.id:
            await offers_repo.create_offer_for_service(
                new_offer=OfferCreate(
                    service_id=created_service.id, user_id=user.id
                )
            )

    return created_service


@pytest_asyncio.fixture
async def test_service_with_accepted_offer(
    db: Database, user_darlene: UserInDB, user_mr_robot: UserInDB,
    test_user_list: List[UserInDB]
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    offers_repo = OffersRepository(db)

    new_service = ServiceCreate(
        name="service with offers",
        description="lorem ipsum",
        price=9.99,
        category="full_clean"
    )

    created_service = await service_repo.create_service(
        new_service=new_service, requesting_user=user_darlene
    )

    offers = []

    for user in test_user_list:
        offers.append(
            await offers_repo.create_offer_for_service(
                new_offer=OfferCreate(
                    service_id=created_service.id,
                    user_id=user.id
                )
            )
        )

    await offers_repo.accept_offer(
        offer=[o for o in offers if o.user_id == user_mr_robot.id][0],
    )

    return created_service


async def create_service_with_evaluated_offer_helper(
    db: Database,
    owner: UserInDB,
    cleaner: UserInDB,
    service_create: ServiceCreate,
    eval_create: EvaluationCreate
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    offers_repo = OffersRepository(db)
    eval_repo = EvaluationsRepository(db)

    created_service = await service_repo.create_service(
        new_service=service_create,
        requesting_user=owner
    )

    offer = await offers_repo.create_offer_for_service(
        new_offer=OfferCreate(
            service_id=created_service.id,
            user_id=cleaner.id
        )
    )

    await offers_repo.accept_offer(
        offer=offer,
        # offer_update=OfferUpdate(status="accepted")
    )

    await eval_repo.create_evaluation_for_cleaner(
        evaluation_create=eval_create,
        service=created_service,
        cleaner=cleaner
    )

    return created_service


@pytest_asyncio.fixture
async def test_list_of_services_with_evaluated_offer(
    db: Database,
    user_darlene: UserInDB,
    user_mr_robot: UserInDB,
) -> List[ServiceInDB]:
    return [
        await create_service_with_evaluated_offer_helper(
            db=db,
            owner=user_darlene,
            cleaner=user_mr_robot,
            service_create=ServiceCreate(
                name=f"test service - {i}",
                description=f"test description - {i}",
                price=float(f"{i}9.99"),
                category="full_clean",

            ),
            eval_create=EvaluationCreate(
                professionalism=random.randint(1,5),
                completeness=random.randint(1,5),
                efficiency=random.randint(1,5),
                overall_rating=random.randint(1,5),
                headline=f"test headline - {i}",
                comment=f"test comment - {i}",

            )
        )
        for i in range(5)
    ]


@pytest_asyncio.fixture
async def test_list_of_new_and_updated_services(db: Database, test_user_list: List[UserInDB]) -> List[ServiceInDB]:
    services_repo = ServicesRepository(db)
    new_services = [
        await services_repo.create_service(
            new_service=ServiceCreate(
                name=f"feed item service job - {i}",
                description=f"test description for feed item service: {i}",
                price=float(f"{i}9.99"),
                category=["full_clean", "spot_clean", "dust_up"][i % 3],
            ),
            requesting_user=test_user_list[i % len(test_user_list)],
        )
        for i in range(50)
    ]
    # update every 4 services
    for i, service in enumerate(new_services):
        if i % 4 == 0:
            updated_service = await services_repo.update_service(
                service=service,
                service_update=ServiceUpdate(
                    description=f"Updated {service.description}", price=service.price + 100.0
                ),
            )
            new_services[i] = updated_service
    return new_services

