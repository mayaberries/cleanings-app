import datetime
from typing import Optional
from pydantic import field_validator

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.user import UserPublic


class PetProfileBase(CoreModel):
    name: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    birth_date: Optional[datetime.date] = None
    notes: Optional[str] = None
    image: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def name_is_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not value.strip():
            raise ValueError("Pet name cannot be blank.")
        return value


class PetProfileCreate(PetProfileBase):
    name: str


class PetProfileUpdate(PetProfileBase):
    pass


class PetProfileInDB(IDModelMixin, PetProfileBase, DateTimeModelMixin):
    name: str
    owner: str


class PetProfilePublic(PetProfileInDB):
    owner: Optional["str | UserPublic"] = None