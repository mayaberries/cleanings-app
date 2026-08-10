import datetime
import random
from typing import List

import pytest_asyncio
from databases import Database

from app.db.repositories.evaluations import EvaluationsRepository
from app.db.repositories.appointments import AppointmentsRepository
from app.db.repositories.services import ServicesRepository
from app.models.appointments.evaluation import EvaluationCreate
from app.models.appointments.appointment import AppointmentCreate
from app.models.services.service import ServiceCreate, ServiceInDB, ServiceUpdate
from app.models.auth.user import UserInDB
from tests._fixtures.pets import create_pet_for_user


def _unique_future_base_time() -> datetime.datetime:
    """
    Anchored far enough into a random future window that concurrent/adjacent
    test runs sharing the same (non-reset) test DB won't collide on
    overlapping confirmed appointments for the same provider.
    """
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=random.randint(2, 3650), hours=random.randint(0, 23)
    )


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
async def test_service_with_appointments(
        db: Database,
        user_clinic_a_admin: UserInDB,
        test_client_list: List[UserInDB]
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    appts_repo = AppointmentsRepository(db)

    new_service = ServiceCreate(
        name="service with appointments", description="lorem ipsum", price=9.99, category="dental_cleaning"
    )
    created_service = await service_repo.create_service(
        new_service=new_service, requesting_user=user_clinic_a_admin
    )

    base_time = _unique_future_base_time()

    for i, user in enumerate(test_client_list):
        pet = await create_pet_for_user(db, user, name=f"Pet {i}")  # NEW
        await appts_repo.create_appointment_for_service(
            new_appointment=AppointmentCreate(
                service_id=created_service.id,
                user_id=user.id,
                pet_id=pet.id,  # NEW
                start_time=base_time + datetime.timedelta(hours=i),
            ),
            service=created_service,
        )

    return created_service


@pytest_asyncio.fixture
async def test_service_with_accepted_appointment(
        db: Database,
        user_clinic_a_admin: UserInDB,
        user_client_one: UserInDB,
        test_client_list: List[UserInDB]
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    appts_repo = AppointmentsRepository(db)

    new_service = ServiceCreate(
        name="service with appointments", description="lorem ipsum", price=9.99, category="dental_cleaning"
    )
    created_service = await service_repo.create_service(
        new_service=new_service, requesting_user=user_clinic_a_admin
    )

    base_time = _unique_future_base_time()
    appointments = []

    for i, user in enumerate(test_client_list):
        pet = await create_pet_for_user(db, user, name=f"Pet {i}")  # NEW
        appointments.append(
            await appts_repo.create_appointment_for_service(
                new_appointment=AppointmentCreate(
                    service_id=created_service.id,
                    user_id=user.id,
                    pet_id=pet.id,  # NEW
                    start_time=base_time + datetime.timedelta(hours=i),
                ),
                service=created_service,
            )
        )

    await appts_repo.confirm_appointment(
        appointment=[a for a in appointments if a.user_id == user_client_one.id][0],
    )

    return created_service


async def create_service_with_evaluated_appointment_helper(
        db: Database, owner: UserInDB, cleaner: UserInDB,
        service_create: ServiceCreate, eval_create: EvaluationCreate
) -> ServiceInDB:
    service_repo = ServicesRepository(db)
    appts_repo = AppointmentsRepository(db)
    eval_repo = EvaluationsRepository(db)

    created_service = await service_repo.create_service(new_service=service_create, requesting_user=owner)
    pet = await create_pet_for_user(db, cleaner, name="Evaluated Pet")  # NEW

    appointment = await appts_repo.create_appointment_for_service(
        new_appointment=AppointmentCreate(
            service_id=created_service.id,
            user_id=cleaner.id,
            pet_id=pet.id,  # NEW
            start_time=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1),
        ),
        service=created_service,
    )

    confirmed_appointment = await appts_repo.confirm_appointment(appointment=appointment)
    await eval_repo.create_evaluation_for_appointment(evaluation_create=eval_create, appointment=confirmed_appointment)
    return created_service


@pytest_asyncio.fixture
async def test_list_of_services_with_evaluated_appointment(
        db: Database,
        user_clinic_a_admin: UserInDB,
        user_client_one: UserInDB,
) -> List[ServiceInDB]:
    return [
        await create_service_with_evaluated_appointment_helper(
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
