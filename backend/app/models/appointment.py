import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr, field_validator

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


def _validate_start_time_in_future(value: datetime.datetime) -> datetime.datetime:
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
        return _validate_start_time_in_future(value)


class PublicAppointmentCreate(CoreModel):
    """
    Request body for POST /api/public/appointments (public_booking.py).
    Deliberately not inheriting ProfileBase -- this is the contact subset
    of that model (full_name, phone_number) plus email, kept lean for a
    booking-widget form rather than dragging in bio/image fields that make
    no sense here. UsersRepository.get_or_create_guest_user is what
    actually threads full_name/phone_number into a real Profile record,
    same table/model a logged-in user's contact info lives in.
    """
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    service_id: str
    start_time: datetime.datetime

    @field_validator("start_time")
    @classmethod
    def start_time_must_be_in_the_future(cls, value: datetime.datetime) -> datetime.datetime:
        return _validate_start_time_in_future(value)