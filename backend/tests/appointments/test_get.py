import random
import uuid
from typing import List, Callable

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.appointments import AppointmentsRepository
from app.models.appointments.appointment import AppointmentPublic
from app.models.services.service import ServiceInDB
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


class TestGetAppointments:
    async def test_service_owner_can_get_appointment_from_user(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_service_with_appointments: ServiceInDB,
    ) -> None:
        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        selected = random.choice(appointments)

        response = await clinic_a_admin_client.get(
            app.url_path_for(
                "appointments:get-appointment-by-id",
                service_id=test_service_with_appointments.id,
                appointment_id=selected.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        appointment = AppointmentPublic(**response.json())

        assert appointment.id == selected.id

    async def test_appointment_owner_can_get_own_appointment(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB,

    ) -> None:
        first_test_user = test_client_list[0]

        authorized_client = create_authorized_client(user=first_test_user)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        own_appointment = [a for a in appointments if a.user_id == first_test_user.id][0]

        response = await authorized_client.get(
            app.url_path_for(
                "appointments:get-appointment-by-id",
                service_id=test_service_with_appointments.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        appointment = AppointmentPublic(**response.json())

        assert appointment.user_id == first_test_user.id

    async def test_other_authenticated_users_cant_view_appointment_from_user(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB,
    ) -> None:
        first_test_user = test_client_list[0]
        second_test_user = test_client_list[1]

        authorized_client = create_authorized_client(user=first_test_user)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        other_appointment = [a for a in appointments if a.user_id == second_test_user.id][0]

        response = await authorized_client.get(
            app.url_path_for(
                "appointments:get-appointment-by-id",
                service_id=test_service_with_appointments.id,
                appointment_id=other_appointment.id,
            )
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_service_owner_can_get_all_appointments_for_services(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB,
    ) -> None:
        response = await clinic_a_admin_client.get(
            app.url_path_for("appointments:list-appointments-for-service", service_id=test_service_with_appointments.id)
        )

        assert response.status_code == status.HTTP_200_OK

        for appointment in response.json():
            assert appointment["user_id"] in [user.id for user in test_client_list]

    async def test_non_owners_forbidden_from_fetching_all_appointments_for_service(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_appointments: ServiceInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.get(
            app.url_path_for(
                "appointments:list-appointments-for-service",
                service_id=test_service_with_appointments.id
            )
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
