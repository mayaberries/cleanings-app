from typing import Optional
from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin


class ClinicBase(CoreModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class ClinicCreate(ClinicBase):
    name: str


class ClinicUpdate(ClinicBase):
    pass


class ClinicInDB(IDModelMixin, DateTimeModelMixin, ClinicBase):
    name: str


class ClinicPublic(IDModelMixin, DateTimeModelMixin, ClinicBase):
    name: str
