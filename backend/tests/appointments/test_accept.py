import random
from typing import List, Callable

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.appointments import AppointmentsRepository
from app.models.appointment import AppointmentPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

class TestAcceptAppointments:
    async def test_service_owner_can_accept_offer_succesfully(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        selected = random.choice(appointments)

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment",
                service_id=test_service_with_appointments.id,
                appointment_id=selected.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        accepted_offer = AppointmentPublic(**response.json())

        assert accepted_offer.status == "confirmed"
        assert accepted_offer.id == selected.id
        assert accepted_offer.service_id == test_service_with_appointments.id

    async def test_non_owner_forbidden_from_accepting_offer_for_service(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        selected = random.choice(appointments)

        response = await authorized_client.put(
            app.url_path_for(
                "appointments:confirm-appointment",
                service_id=test_service_with_appointments.id,
                appointment_id=selected.id,
            )
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_service_owner_cant_confirm_overlapping_appointment(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)

        # confirm the first one
        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment",
                service_id=test_service_with_appointments.id,
                appointment_id=appointments[0].id,
            )
        )
        assert response.status_code == status.HTTP_200_OK

        # manufacture a second appointment that overlaps the first, then try
        # to confirm it too
        overlapping = await appts_repo.create_appointment_for_service(
            new_appointment=__import__("app.models.appointment", fromlist=["AppointmentCreate"]).AppointmentCreate(
                service_id=test_service_with_appointments.id,
                user_id=test_client_list[0].id,
                start_time=appointments[0].start_time,
            ),
            service=test_service_with_appointments,
        )

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment",
                service_id=test_service_with_appointments.id,
                appointment_id=overlapping.id,
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_confirming_one_offer_does_not_affect_others(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        selected = random.choice(appointments)

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment",
                service_id=test_service_with_appointments.id,
                appointment_id=selected.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        response = await clinic_a_admin_client.get(
            app.url_path_for(
                "appointments:list-appointments-for-service",
                service_id=test_service_with_appointments.id
            )
        )

        assert response.status_code == status.HTTP_200_OK

        refreshed = [AppointmentPublic(**o) for o in response.json()]

        for appt in refreshed:
            if appt.id == selected.id:
                assert appt.status == "confirmed"
            else:
                # non-overlapping requests are left untouched, not auto-declined
                assert appt.status == "requested"
