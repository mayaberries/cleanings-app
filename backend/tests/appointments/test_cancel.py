import uuid
from typing import Callable

import pytest
from fastapi import FastAPI, status

from app.db.repositories.appointments import AppointmentsRepository
from app.models.appointment import AppointmentPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestCancelAppointments:
    async def test_user_can_cancel_offer_after_it_has_been_accepted(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        accepted_user_client = create_authorized_client(user=user_client_one)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_accepted_appointment)
        own_appointment = [a for a in appointments if a.user_id == user_client_one.id][0]

        response = await accepted_user_client.put(
            app.url_path_for(
                "appointments:cancel-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        cancelled_offer = AppointmentPublic(**response.json())

        assert cancelled_offer.status == "cancelled"
        assert cancelled_offer.user_id == user_client_one.id
        assert cancelled_offer.service_id == test_service_with_accepted_appointment.id

    async def test_only_accepted_appointments_can_be_cancelled(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_two: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        accepted_user_client = create_authorized_client(user=user_client_two)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_accepted_appointment)
        own_appointment = [a for a in appointments if a.user_id == user_client_two.id][0]

        response = await accepted_user_client.put(
            app.url_path_for(
                "appointments:cancel-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_canceling_offer_does_not_affect_others(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        accepted_user_client = create_authorized_client(user=user_client_one)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_accepted_appointment)
        own_appointment = [a for a in appointments if a.user_id == user_client_one.id][0]

        response = await accepted_user_client.put(
            app.url_path_for(
                "appointments:cancel-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        appointments = await appts_repo.list_appointments_for_service(
            service=test_service_with_accepted_appointment
        )

        for appt in appointments:
            if appt.user_id == user_client_one.id:
                assert appt.status == "cancelled"
            else:
                assert appt.status == "requested"
