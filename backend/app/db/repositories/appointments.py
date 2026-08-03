from typing import List, Union
from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository

from app.models.appointment import (
    AppointmentCreate,
    AppointmentPublic,
    AppointmentInDB,
    AppointmentStatus,
)
from app.models.service import ServiceInDB
from app.models.user import UserInDB

CREATE_APPOINTMENT_FOR_SERVICE_QUERY = """
    INSERT INTO appointments (service_id, user_id, status)
    VALUES (:service_id, :user_id, :status)
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

LIST_APPOINTMENTS_FOR_SERVICE_QUERY = """
    SELECT service_id, user_id, status, created_at, updated_at
    FROM appointments
    WHERE service_id = :service_id;
"""

GET_APPOINTMENT_FOR_SERVICE_FROM_USER_QUERY = """
    SELECT service_id, user_id, status, created_at, updated_at
    FROM appointments
    WHERE service_id = :service_id AND user_id = :user_id;
"""

CONFIRM_APPOINTMENT_QUERY = """
    UPDATE appointments
    SET status = 'confirmed'
    WHERE service_id = :service_id AND user_id = :user_id
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

DECLINE_ALL_OTHER_PENDING_APPOINTMENTS_QUERY = """
    UPDATE appointments
    SET status = 'declined'
    WHERE service_id = :service_id
    AND user_id != :user_id
    AND status = 'requested';
"""

CANCEL_APPOINTMENT_QUERY = """
    UPDATE appointments
    SET status = 'cancelled'
    WHERE service_id = :service_id AND user_id = :user_id
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

SET_ALL_OTHER_APPOINTMENTS_AS_REQUESTED_QUERY = """
    UPDATE appointments
    SET status = 'requested'
    WHERE service_id = :service_id 
    AND user_id != :user_id 
    AND status = 'declined'
"""

WITHDRAW_APPOINTMENT_QUERY = """
    DELETE FROM appointments
    WHERE service_id = :service_id
    AND user_id = :user_id
    RETURNING service_id, user_id, status, created_at, updated_at;
"""

MARK_AS_COMPLETED_QUERY = """
    UPDATE appointments
    SET status = 'completed'
    WHERE service_id = :service_id AND user_id = :user_id
"""


class AppointmentsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def create_appointment_for_service(self, *, new_appointment: AppointmentCreate) -> AppointmentInDB:
        created_appointment = await self.db.fetch_one(
            query=CREATE_APPOINTMENT_FOR_SERVICE_QUERY,
            values={**new_appointment.model_dump(), "status": AppointmentStatus.requested.value}
        )
        return AppointmentInDB(**created_appointment)

    async def list_appointments_for_service(
            self, *, service: ServiceInDB, populate: bool = True
    ) -> List[Union[AppointmentInDB, AppointmentPublic]]:
        appointment_records = await self.db.fetch_all(
            query=LIST_APPOINTMENTS_FOR_SERVICE_QUERY,
            values={"service_id": service.id}
        )
        appointments = [AppointmentInDB(**a) for a in appointment_records]

        if populate:
            return [await self.populate_appointment(appointment=appointment) for appointment in appointments]

        return appointments

    async def get_appointment_for_service_from_user(self, *, service: ServiceInDB, user: UserInDB) -> AppointmentInDB:
        appointment_record = await self.db.fetch_one(
            query=GET_APPOINTMENT_FOR_SERVICE_FROM_USER_QUERY,
            values={"service_id": service.id, "user_id": user.id}
        )

        if not appointment_record:
            return None

        return AppointmentInDB(**appointment_record)

    async def confirm_appointment(self, *, appointment: AppointmentInDB) -> AppointmentInDB:
        async with self.db.transaction():
            confirmed_appointment = await self.db.fetch_one(
                query=CONFIRM_APPOINTMENT_QUERY,
                values={"service_id": appointment.service_id,
                        "user_id": appointment.user_id}
            )

            await self.db.execute(
                query=DECLINE_ALL_OTHER_PENDING_APPOINTMENTS_QUERY,
                values={"service_id": appointment.service_id,
                        "user_id": appointment.user_id}
            )

            return AppointmentInDB(**confirmed_appointment)

    async def cancel_appointment(self, *, appointment: AppointmentInDB) -> AppointmentInDB:
        async with self.db.transaction():
            cancelled_appointment = await self.db.fetch_one(
                query=CANCEL_APPOINTMENT_QUERY,
                values={"service_id": appointment.service_id,
                        "user_id": appointment.user_id}
            )

            await self.db.execute(
                query=SET_ALL_OTHER_APPOINTMENTS_AS_REQUESTED_QUERY,
                values={"service_id": appointment.service_id,
                        "user_id": appointment.user_id}
            )

            return AppointmentInDB(**cancelled_appointment)

    async def withdraw_appointment(self, *, appointment: AppointmentInDB) -> AppointmentInDB:
        withdrawn_appointment = await self.db.fetch_one(
            query=WITHDRAW_APPOINTMENT_QUERY,
            values={
                "service_id": appointment.service_id,
                "user_id": appointment.user_id
            }
        )
        return AppointmentInDB(**withdrawn_appointment)

    async def mark_as_completed(self, *, service: ServiceInDB, cleaner: UserInDB) -> None:
        return await self.db.execute(
            query=MARK_AS_COMPLETED_QUERY,
            values={
                "service_id": service.id,
                "user_id": cleaner.id
            }
        )

    async def populate_appointment(self, *, appointment: AppointmentInDB) -> AppointmentPublic:
        return AppointmentPublic(
            **appointment.model_dump(),
            user=await self.users_repo.get_user_by_id(
                user_id=appointment.user_id
            )
        )