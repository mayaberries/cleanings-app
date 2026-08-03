from typing import Optional, Union
from enum import Enum

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.user import UserPublic


class CleaningType(str, Enum):
    dust_up = "dust_up"
    spot_clean = "spot_clean"
    full_clean = "full_clean"


class CleaningBase(CoreModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cleaning_type: Optional[CleaningType] = CleaningType.spot_clean


class CleaningCreate(CleaningBase):
    name: str
    price: float


class CleaningUpdate(CleaningBase):
    cleaning_type: Optional[CleaningType] = None


class CleaningInDB(IDModelMixin, CleaningBase, DateTimeModelMixin):
    name: str
    price: float
    cleaning_type: CleaningType
    owner: str


class CleaningPublic(IDModelMixin, CleaningBase):
    owner: Union[str, UserPublic]