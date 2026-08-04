from fastapi import FastAPI

from app.db.repositories.appointments import AppointmentsRepository
from app.models.service import ServiceInDB
from app.models.user import UserInDB


async def get_appointment_for(app: FastAPI, service: ServiceInDB, user: UserInDB):
    appts_repo = AppointmentsRepository(app.state._db)
    appointments = await appts_repo.list_appointments_for_service(service=service)
    return [a for a in appointments if a.user_id == user.id][0]

