from typing import List, Callable

import pytest
from fastapi import FastAPI, status

from app.db.repositories.appointments import AppointmentsRepository
from app.models.services.service import ServiceInDB
from app.models.auth.user import UserInDB

pytestmark = pytest.mark.asyncio


class TestRescindAppointments:
    async def test_user_can_successfully_rescind_pending_appt(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_two: UserInDB,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_appointments)
        own_appointment = [a for a in appointments if a.user_id == user_client_two.id][0]

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment",
                service_id=test_service_with_appointments.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        remaining = await appts_repo.list_appointments_for_service(
            service=test_service_with_appointments
        )

        remaining_ids = [a.id for a in remaining]
        assert own_appointment.id not in remaining_ids

    async def test_users_cannot_rescind_accepted_appointments(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_accepted_appointment)
        own_appointment = [a for a in appointments if a.user_id == user_client_one.id][0]

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_users_cannot_rescind_cancelled_appointments(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_accepted_appointment)
        own_appointment = [a for a in appointments if a.user_id == user_client_one.id][0]

        response = await authorized_client.put(
            app.url_path_for(
                "appointments:cancel-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=own_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_users_cannot_rescind_confirmed_appointments_of_others(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_two: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        appts_repo = AppointmentsRepository(app.state._db)
        appointments = await appts_repo.list_appointments_for_service(service=test_service_with_accepted_appointment)
        others_appointment = [a for a in appointments if a.user_id != user_client_two.id][0]

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment",
                service_id=test_service_with_accepted_appointment.id,
                appointment_id=others_appointment.id,
            )
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
