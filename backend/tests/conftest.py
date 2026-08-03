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

from app.models.user import UserInDB

from app.models.offer import OfferCreate
from app.db.repositories.offers import OffersRepository

from app.models.evaluation import EvaluationCreate
from app.db.repositories.evaluations import EvaluationsRepository

pytest_plugins = ["tests.fixtures.users"]


@pytest_asyncio.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")


@pytest_asyncio.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application
    return get_application()


@pytest_asyncio.fixture
def db(app: FastAPI) -> Database:
    return app.state._db


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
async def test_service(db: Database, user_clinic_a_admin: UserInDB) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    new_service = ServiceCreate(
        name="fake service name",
        description="fake service description",
        price=9.99,
        category="wellness_exam",
    )
    return await service_repo.create_service(new_service=new_service, requesting_user=user_clinic_a_admin)


@pytest_asyncio.fixture
async def test_service_with_offers(
        db: Database,
        user_clinic_a_admin: UserInDB,
        test_client_list: List[UserInDB]
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    offers_repo = OffersRepository(db)

    new_service = ServiceCreate(
        name="service with offers", description="lorem ipsum", price=9.99, category="dental_cleaning"
    )

    created_service = await service_repo.create_service(
        new_service=new_service, requesting_user=user_clinic_a_admin
    )

    for user in test_client_list:
        await offers_repo.create_offer_for_service(
            new_offer=OfferCreate(
                service_id=created_service.id, user_id=user.id
            )
        )

    return created_service


@pytest_asyncio.fixture
async def test_service_with_accepted_offer(
        db: Database,
        user_clinic_a_admin: UserInDB,
        user_client_one: UserInDB,
        test_client_list: List[UserInDB]
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    offers_repo = OffersRepository(db)

    new_service = ServiceCreate(
        name="service with offers",
        description="lorem ipsum",
        price=9.99,
        category="dental_cleaning"
    )

    created_service = await service_repo.create_service(
        new_service=new_service, requesting_user=user_clinic_a_admin
    )

    offers = []

    for user in test_client_list:
        offers.append(
            await offers_repo.create_offer_for_service(
                new_offer=OfferCreate(
                    service_id=created_service.id,
                    user_id=user.id
                )
            )
        )

    await offers_repo.accept_offer(
        offer=[o for o in offers if o.user_id == user_client_one.id][0],
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

    await offers_repo.accept_offer(offer=offer)

    await eval_repo.create_evaluation_for_cleaner(
        evaluation_create=eval_create,
        service=created_service,
        cleaner=cleaner
    )

    return created_service


@pytest_asyncio.fixture
async def test_list_of_services_with_evaluated_offer(
        db: Database,
        user_clinic_a_admin: UserInDB,
        user_client_one: UserInDB,
) -> List[ServiceInDB]:
    return [
        await create_service_with_evaluated_offer_helper(
            db=db,
            owner=user_clinic_a_admin,
            cleaner=user_client_one,
            service_create=ServiceCreate(
                name=f"test service - {i}",
                description=f"test description - {i}",
                price=float(f"{i}9.99"),
                category="dental_cleaning",
            ),
            eval_create=EvaluationCreate(
                professionalism=random.randint(1, 5),
                completeness=random.randint(1, 5),
                efficiency=random.randint(1, 5),
                overall_rating=random.randint(1, 5),
                headline=f"test headline - {i}",
                comment=f"test comment - {i}",
            )
        )
        for i in range(5)
    ]


@pytest_asyncio.fixture
async def test_list_of_new_and_updated_services(
        db: Database, clinic_a_staff: List[UserInDB], clinic_b_staff: List[UserInDB]
) -> List[ServiceInDB]:
    services_repo = ServicesRepository(db)
    all_staff = clinic_a_staff + clinic_b_staff
    new_services = [
        await services_repo.create_service(
            new_service=ServiceCreate(
                name=f"feed item service job - {i}",
                description=f"test description for feed item service: {i}",
                price=float(f"{i}9.99"),
                category=["wellness_exam", "vaccination", "dental_cleaning"][i % 3],
            ),
            requesting_user=all_staff[i % len(all_staff)],
        )
        for i in range(50)
    ]
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
