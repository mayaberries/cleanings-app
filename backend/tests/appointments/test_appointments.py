import datetime
import random
import uuid
from typing import List, Callable

import pytest
from fastapi import FastAPI, status
from httpx import AsyncClient

from app.db.repositories.appointments import AppointmentsRepository
from app.models.appointment import AppointmentPublic
from app.models.service import ServiceInDB
from app.models.user import UserInDB

pytestmark = pytest.mark.asyncio

FAKE_ID = str(uuid.uuid4())


def future_time(hours: int = 1) -> str:
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=hours)).isoformat()


class TestAppointmentRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.post(app.url_path_for("appointments:create-appointment", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("appointments:list-appointments-for-service", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(
            app.url_path_for("appointments:get-appointment-by-id", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(
            app.url_path_for("appointments:confirm-appointment", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(
            app.url_path_for("appointments:cancel-appointment", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.delete(
            app.url_path_for("appointments:withdraw-appointment", service_id=1, appointment_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestCreateappointments:
    async def test_user_can_successfully_create_offer_for_other_users_service_job(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_one: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )
        assert response.status_code == status.HTTP_201_CREATED

        offer = AppointmentPublic(**response.json())
        assert offer.user_id == user_client_one.id
        assert offer.service_id == test_service.id
        assert offer.status == "requested"

    async def test_user_can_create_multiple_appointments_for_same_service(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_two: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response_one = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(hours=1)},
        )
        assert response_one.status_code == status.HTTP_201_CREATED

        response_two = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time(hours=5)},
        )
        assert response_two.status_code == status.HTTP_201_CREATED
        assert response_two.json()["id"] != response_one.json()["id"]

    async def test_user_unable_to_create_offer_for_their_own_service_job(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB,
            test_service: ServiceInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_unauthenticated_users_cant_create_appointments(
            self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB,
    ) -> None:
        response = await client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id),
            json={"start_time": future_time()},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "id, status_code",
        (
                (FAKE_ID, 404),
                (None, 404)
        ),
    )
    async def test_wrong_id_gives_proper_error_status(
            self, app: FastAPI, create_authorized_client: Callable, user_client_three: UserInDB, id: str,
            status_code: int
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_three)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=id),
            json={"start_time": future_time()},
        )

        assert response.status_code == status_code


class TestGetappointments:
    async def test_service_owner_can_get_offer_from_user(
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

        offer = AppointmentPublic(**response.json())

        assert offer.id == selected.id

    async def test_offer_owner_can_get_own_offer(
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

    async def test_other_authenticated_users_cant_view_offer_from_user(
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

        for offer in response.json():
            assert offer["user_id"] in [user.id for user in test_client_list]

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


class TestAcceptappointments:
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


class TestCancelappointments:
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


class TestRescindappointments:
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