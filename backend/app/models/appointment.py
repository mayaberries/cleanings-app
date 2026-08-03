from enum import Enum
from typing import Optional
from app.models.core import CoreModel, DateTimeModelMixin
from app.models.user import UserPublic
from app.models.service import ServicePublic


class AppointmentStatus(str, Enum):
    requested = "requested"
    confirmed = "confirmed"
    declined = "declined"
    cancelled = "cancelled"
    completed = "completed"


class AppointmentBase(CoreModel):
    user_id: Optional[str] = None
    service_id: Optional[str] = None
    status: Optional[AppointmentStatus] = AppointmentStatus.requested


class AppointmentCreate(AppointmentBase):
    user_id: str
    service_id: str


class AppointmentUpdate(CoreModel):
    status: AppointmentStatus


class AppointmentInDB(DateTimeModelMixin, AppointmentBase):
    user_id: str
    service_id: str


class AppointmentPublic(AppointmentInDB):
    user: Optional[UserPublic] = None
    service: Optional[ServicePublic] = None