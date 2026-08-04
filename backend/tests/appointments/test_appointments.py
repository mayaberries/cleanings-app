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


class TestAppointmentRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        response = await client.post(app.url_path_for("appointments:create-appointment", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(app.url_path_for("appointments:list-appointments-for-service", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.get(
            app.url_path_for("appointments:get-appointment-from-user", service_id=1, username="bradpitt"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(
            app.url_path_for("appointments:confirm-appointment-from-user", service_id=1, username="braddpit"))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.put(app.url_path_for("appointments:cancel-appointment-from-user", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND

        response = await client.delete(app.url_path_for("appointments:withdraw-appointment-from-user", service_id=1))
        assert response.status_code != status.HTTP_404_NOT_FOUND


class TestCreateappointments:
    async def test_user_can_successfully_create_offer_for_other_users_service_job(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_one: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id)
        )
        assert response.status_code == status.HTTP_201_CREATED

        offer = AppointmentPublic(**response.json())
        assert offer.user_id == user_client_one.id
        assert offer.service_id == test_service.id
        assert offer.status == "requested"

    async def test_user_cant_create_duplicate_appointments(
            self, app: FastAPI, create_authorized_client: Callable, test_service: ServiceInDB,
            user_client_two: UserInDB,
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id)
        )
        assert response.status_code == status.HTTP_201_CREATED

        response = await authorized_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id)
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_user_unable_to_create_offer_for_their_own_service_job(
            self, app: FastAPI, clinic_a_admin_client: AsyncClient, user_clinic_a_admin: UserInDB,
            test_service: ServiceInDB
    ) -> None:
        response = await clinic_a_admin_client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id)
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_unauthenticated_users_cant_create_appointments(
            self, app: FastAPI, client: AsyncClient, test_service: ServiceInDB,
    ) -> None:
        response = await client.post(
            app.url_path_for("appointments:create-appointment", service_id=test_service.id)
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
            app.url_path_for("appointments:create-appointment", service_id=id)
        )

        assert response.status_code == status_code


class TestGetappointments:
    async def test_service_owner_can_get_offer_from_user(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB,
    ) -> None:
        selected_user = random.choice(test_client_list)

        response = await clinic_a_admin_client.get(
            app.url_path_for(
                "appointments:get-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=selected_user.username,
            )
        )

        assert response.status_code == status.HTTP_200_OK

        offer = AppointmentPublic(**response.json())

        assert offer.user_id == selected_user.id

    async def test_offer_owner_can_get_own_offer(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB,

    ) -> None:
        first_test_user = test_client_list[0]

        authorized_client = create_authorized_client(user=first_test_user)

        response = await authorized_client.get(
            app.url_path_for(
                "appointments:get-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=first_test_user.username
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

        response = await authorized_client.get(
            app.url_path_for(
                "appointments:get-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=second_test_user.username,
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
        selected_user = random.choice(test_client_list)

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=selected_user.username
            )
        )

        assert response.status_code == status.HTTP_200_OK

        accepted_offer = AppointmentPublic(**response.json())

        assert accepted_offer.status == "confirmed"
        assert accepted_offer.user_id == selected_user.id
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
        selected_user = random.choice(test_client_list)

        response = await authorized_client.put(
            app.url_path_for(
                "appointments:confirm-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=selected_user.username
            )
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    async def test_service_owner_cant_accept_multiple_appointments(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=test_client_list[0].username
            )
        )

        assert response.status_code == status.HTTP_200_OK

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=test_client_list[1].username
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_accepting_one_offer_rejects_all_other_appointments(
            self,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_client_list: List[UserInDB],
            test_service_with_appointments: ServiceInDB
    ) -> None:
        selected_user = random.choice(test_client_list)

        response = await clinic_a_admin_client.put(
            app.url_path_for(
                "appointments:confirm-appointment-from-user",
                service_id=test_service_with_appointments.id,
                username=selected_user.username
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

        appointments = [AppointmentPublic(**o) for o in response.json()]

        for appt in appointments:
            if appt.user_id == selected_user.id:
                assert appt.status == "confirmed"
            else:
                assert appt.status == "declined"


class TestCancelAppointments:
    async def test_user_can_cancel_offer_after_it_has_been_accepted(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        accepted_user_client = create_authorized_client(user=user_client_one)

        response = await accepted_user_client.put(
            app.url_path_for(
                "appointments:cancel-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
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

        response = await accepted_user_client.put(
            app.url_path_for(
                "appointments:cancel-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_canceling_offer_sets_all_others_to_pending(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        accepted_user_client = create_authorized_client(user=user_client_one)

        response = await accepted_user_client.put(
            app.url_path_for(
                "appointments:cancel-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
            )
        )

        assert response.status_code == status.HTTP_200_OK

        appts_repo = AppointmentsRepository(app.state._db)

        appointments = await appts_repo.list_appointments_for_service(
            service=test_service_with_accepted_appointment
        )

        for appt in appointments:
            if appt.user_id == user_client_one.id:
                assert appt.status == "cancelled"
            else:
                assert appt.status == "requested"


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

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment-from-user",
                service_id=test_service_with_appointments.id
            )
        )

        assert response.status_code == status.HTTP_200_OK

        appointments_repo = AppointmentsRepository(app.state._db)

        appointments = await appointments_repo.list_appointments_for_service(
            service=test_service_with_appointments
        )

        user_ids = [user.id for user in test_client_list]

        for offer in appointments:
            assert offer.user_id in user_ids
            assert offer.user_id != user_client_two.id

    async def test_users_cannot_rescind_accepted_appointments(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_one: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_one)

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
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

        response = await authorized_client.put(
            app.url_path_for(
                "appointments:cancel-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
            )
        )

        assert response.status_code == status.HTTP_200_OK

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_users_cannot_rescind_rejected_appointments(
            self,
            app: FastAPI,
            create_authorized_client: Callable,
            user_client_two: UserInDB,
            test_service_with_accepted_appointment: ServiceInDB
    ) -> None:
        authorized_client = create_authorized_client(user=user_client_two)

        response = await authorized_client.delete(
            app.url_path_for(
                "appointments:withdraw-appointment-from-user",
                service_id=test_service_with_accepted_appointment.id
            )
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
