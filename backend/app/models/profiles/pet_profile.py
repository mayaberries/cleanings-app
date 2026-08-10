import datetime
from typing import Optional
from pydantic import field_validator

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin
from app.models.profiles.owner_profile import OwnerProfilePublic


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
    # owner_profile_id intentionally NOT here — it's resolved server-side
    # from the requesting owner's own profile, not supplied by the client.


class PetProfileUpdate(PetProfileBase):
    pass


class PetProfileInDB(IDModelMixin, PetProfileBase, DateTimeModelMixin):
    name: str
    owner_profile_id: str


class PetProfilePublic(PetProfileInDB):
    owner_profile_id: Optional["str | OwnerProfilePublic"] = None


class ClinicPetProfileCreate(PetProfileCreate):
    owner_profile_id: str


from pydantic import model_validator


class PublicPetInput(CoreModel):
    """Input for attaching a pet to a public/guest booking — either an
    existing pet already registered at this clinic, or a brand-new one
    created under the resolved guest owner. Same XOR shape as
    ClinicOwnerProfileRegistration, applied to pets instead of owners."""
    pet_id: Optional[str] = None
    new_pet: Optional[PetProfileCreate] = None

    @model_validator(mode="after")
    def exactly_one_pet_source(self) -> "PublicPetInput":
        has_id = self.pet_id is not None
        has_new = self.new_pet is not None
        if has_id == has_new:
            raise ValueError(
                "Provide exactly one of pet_id (existing pet) or new_pet (to create one)."
            )
        return self
