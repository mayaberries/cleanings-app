import datetime
from enum import Enum
from typing import Optional
from app.models.core import CoreModel, DateTimeModelMixin, IDModelMixin
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
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    status: Optional[AppointmentStatus] = AppointmentStatus.requested


# What the client sends: just when they want it. service_id/user_id are
# supplied server-side from path + auth, not client input.
class AppointmentCreate(CoreModel):
    user_id: str
    service_id: str
    start_time: datetime.datetime


class AppointmentUpdate(CoreModel):
    status: AppointmentStatus


class AppointmentInDB(IDModelMixin, DateTimeModelMixin, AppointmentBase):
    user_id: str
    service_id: str
    start_time: datetime.datetime
    end_time: datetime.datetime


class AppointmentPublic(AppointmentInDB):
    user: Optional[UserPublic] = None
    service: Optional[ServicePublic] = None