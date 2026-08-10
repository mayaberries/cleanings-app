from typing import Optional
from pydantic import field_validator

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.clinics.clinic import ClinicPublic
from app.models.services.service_categories import normalize_category


class ServiceBase(CoreModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    duration_minutes: Optional[int] = None

    @field_validator("category", mode="before")
    @classmethod
    def category_is_normalized(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return normalize_category(value)


class ServiceCreate(ServiceBase):
    name: str
    price: float
    category: str


class ServiceUpdate(ServiceBase):
    category: Optional[str] = None


class ServiceInDB(IDModelMixin, ServiceBase, DateTimeModelMixin):
    name: str
    price: float
    category: str
    clinic_id: str


class ServicePublic(IDModelMixin, ServiceBase):
    clinic: "str | ClinicPublic"
