from typing import Optional, Union
from enum import Enum

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.user import UserPublic


class ServiceType(str, Enum):
    dust_up = "dust_up"
    spot_clean = "spot_clean"
    full_clean = "full_clean"


class ServiceBase(CoreModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    service_type: Optional[ServiceType] = ServiceType.spot_clean


class ServiceCreate(ServiceBase):
    name: str
    price: float


class ServiceUpdate(ServiceBase):
    service_type: Optional[ServiceType] = None


class ServiceInDB(IDModelMixin, ServiceBase, DateTimeModelMixin):
    name: str
    price: float
    service_type: ServiceType
    owner: str


class ServicePublic(IDModelMixin, ServiceBase):
    owner: Union[str, UserPublic]