from datetime import timedelta, datetime
from typing import List, Optional, Union
from uuid import uuid4
from databases.core import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository

from app.models.appointment import (
    AppointmentCreate,
    AppointmentPublic,
    AppointmentInDB,
    AppointmentStatus, DEFAULT_APPOINTMENT_DURATION_MINUTES,
)
from app.models.service import ServiceInDB
from app.models.user import UserInDB

CREATE_APPOINTMENT_FOR_SERVICE_QUERY = """
    INSERT INTO appointments (id, service_id, user_id, status, start_time, end_time)
    VALUES (:id, :service_id, :user_id, :status, :start_time, :end_time)
    RETURNING id, service_id, user_id, status, start_time, end_time, created_at, updated_at;
"""

GET_APPOINTMENT_BY_ID_QUERY = """
    SELECT id, service_id, user_id, status, start_time, end_time, created_at, updated_at
    FROM appointments
    WHERE id = :id;
"""

LIST_APPOINTMENTS_FOR_SERVICE_QUERY = """
    SELECT id, service_id, user_id, status, start_time, end_time, created_at, updated_at
    FROM appointments
    WHERE service_id = :service_id
    ORDER BY start_time;
"""

# Replaces "does this service already have any appointment from this user" —
# now it's just history, not an identity check.
LIST_APPOINTMENTS_FOR_SERVICE_FROM_USER_QUERY = """
    SELECT id, service_id, user_id, status, start_time, end_time, created_at, updated_at
    FROM appointments
    WHERE service_id = :service_id AND user_id = :user_id
    ORDER BY start_time DESC;
"""

# The core of the new model: is this time range already claimed by a
# *confirmed* appointment for the same provider (across any of their services)?
CHECK_OVERLAPPING_CONFIRMED_APPOINTMENT_QUERY = """
    SELECT a.id
    FROM appointments a
    INNER JOIN services s ON a.service_id = s.id
    WHERE s.owner = :owner
      AND a.status = 'confirmed'
      AND (CAST(:exclude_id AS CHAR(36)) IS NULL OR a.id != CAST(:exclude_id AS CHAR(36)))
      AND a.start_time < :end_time
      AND a.end_time > :start_time
    LIMIT 1;
"""

CONFIRM_APPOINTMENT_QUERY = """
    UPDATE appointments
    SET status = 'confirmed'
    WHERE id = :id
    RETURNING id, service_id, user_id, status, start_time, end_time, created_at, updated_at;
"""

CANCEL_APPOINTMENT_QUERY = """
    UPDATE appointments
    SET status = 'cancelled'
    WHERE id = :id
    RETURNING id, service_id, user_id, status, start_time, end_time, created_at, updated_at;
"""

WITHDRAW_APPOINTMENT_QUERY = """
    DELETE FROM appointments
    WHERE id = :id
    RETURNING id, service_id, user_id, status, start_time, end_time, created_at, updated_at;
"""

MARK_AS_COMPLETED_QUERY = """
    UPDATE appointments
    SET status = 'completed'
    WHERE id = :id
"""


class AppointmentsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def create_appointment_for_service(
            self, *, new_appointment: AppointmentCreate, service: ServiceInDB
    ) -> AppointmentInDB:
        duration = service.duration_minutes or DEFAULT_APPOINTMENT_DURATION_MINUTES
        start_time = new_appointment.start_time
        end_time = start_time + timedelta(minutes=duration)

        created_appointment = await self.db.fetch_one(
            query=CREATE_APPOINTMENT_FOR_SERVICE_QUERY,
            values={
                "id": str(uuid4()),
                "service_id": new_appointment.service_id,
                "user_id": new_appointment.user_id,
                "status": AppointmentStatus.requested.value,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        return AppointmentInDB(**created_appointment)

    async def get_appointment_by_id(self, *, id: str) -> Optional[AppointmentInDB]:
        appointment_record = await self.db.fetch_one(query=GET_APPOINTMENT_BY_ID_QUERY, values={"id": id})
        if appointment_record:
            return AppointmentInDB(**appointment_record)

    async def list_appointments_for_service(
            self, *, service: ServiceInDB, populate: bool = True
    ) -> List[Union[AppointmentInDB, AppointmentPublic]]:
        appointment_records = await self.db.fetch_all(
            query=LIST_APPOINTMENTS_FOR_SERVICE_QUERY, values={"service_id": service.id}
        )
        appointments = [AppointmentInDB(**a) for a in appointment_records]

        if populate:
            return [await self.populate_appointment(appointment=a) for a in appointments]
        return appointments

    async def list_appointments_for_service_from_user(
            self, *, service: ServiceInDB, user: UserInDB
    ) -> List[AppointmentInDB]:
        records = await self.db.fetch_all(
            query=LIST_APPOINTMENTS_FOR_SERVICE_FROM_USER_QUERY,
            values={"service_id": service.id, "user_id": user.id},
        )
        return [AppointmentInDB(**r) for r in records]

    async def has_overlapping_confirmed_appointment(
            self, *, owner: str, start_time: datetime, end_time: datetime, exclude_id: Optional[str] = None
    ) -> bool:
        conflict = await self.db.fetch_one(
            query=CHECK_OVERLAPPING_CONFIRMED_APPOINTMENT_QUERY,
            values={
                "owner": owner,
                "exclude_id": exclude_id,
                "start_time": start_time,
                "end_time": end_time,
            },
        )
        return conflict is not None

    async def confirm_appointment(self, *, appointment: AppointmentInDB) -> AppointmentInDB:
        confirmed = await self.db.fetch_one(query=CONFIRM_APPOINTMENT_QUERY, values={"id": appointment.id})
        return AppointmentInDB(**confirmed)

    async def cancel_appointment(self, *, appointment: AppointmentInDB) -> AppointmentInDB:
        cancelled = await self.db.fetch_one(query=CANCEL_APPOINTMENT_QUERY, values={"id": appointment.id})
        return AppointmentInDB(**cancelled)

    async def withdraw_appointment(self, *, appointment: AppointmentInDB) -> AppointmentInDB:
        withdrawn = await self.db.fetch_one(query=WITHDRAW_APPOINTMENT_QUERY, values={"id": appointment.id})
        return AppointmentInDB(**withdrawn)

    async def mark_as_completed(self, *, appointment: AppointmentInDB) -> None:
        return await self.db.execute(query=MARK_AS_COMPLETED_QUERY, values={"id": appointment.id})

    async def populate_appointment(self, *, appointment: AppointmentInDB) -> AppointmentPublic:
        return AppointmentPublic(
            **appointment.model_dump(),
            user=await self.users_repo.get_user_by_id(user_id=appointment.user_id),
        )
