import datetime
from enum import Enum
from typing import Optional

from pydantic import field_validator

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


class AppointmentCreate(CoreModel):
    user_id: str
    service_id: str
    start_time: datetime.datetime

    @field_validator("start_time")
    @classmethod
    def start_time_must_be_in_the_future(cls, value: datetime.datetime) -> datetime.datetime:
        now = datetime.datetime.now(datetime.timezone.utc)
        if value <= now:
            raise ValueError("start_time must be in the future")
        return value


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


DEFAULT_APPOINTMENT_DURATION_MINUTES = 30


class AppointmentRequestIn(CoreModel):
    start_time: datetime.datetime

    @field_validator("start_time")
    @classmethod
    def start_time_must_be_in_the_future(cls, value: datetime.datetime) -> datetime.datetime:
        now = datetime.datetime.now(datetime.timezone.utc)
        if value <= now:
            raise ValueError("start_time must be in the future")
        return value
