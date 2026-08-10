import datetime
from enum import Enum
from typing import Optional

from pydantic import model_validator

from app.models.core import CoreModel, DateTimeModelMixin, IDModelMixin
from app.models.profiles.owner_profile import OwnerProfileCreate, OwnerProfilePublic


class ClinicOwnerProfileStatus(str, Enum):
    active = "active"
    blocked = "blocked"


class ClinicOwnerProfileBase(CoreModel):
    notes: Optional[str] = None
    status: ClinicOwnerProfileStatus = ClinicOwnerProfileStatus.active
    referred_by: Optional[str] = None


class ClinicOwnerProfileUpdate(CoreModel):
    notes: Optional[str] = None
    status: Optional[ClinicOwnerProfileStatus] = None
    referred_by: Optional[str] = None


class ClinicOwnerProfileInDB(IDModelMixin, DateTimeModelMixin, ClinicOwnerProfileBase):
    clinic_id: str
    owner_profile_id: str
    first_seen_at: datetime.datetime


class ClinicOwnerProfilePublic(ClinicOwnerProfileInDB):
    owner_profile_id: Optional["str | OwnerProfilePublic"] = None


class ClinicOwnerProfileRegistration(CoreModel):
    """Input for registering an owner with a clinic — either link an
    existing (already-deduplicated) owner profile, or create a brand new
    account-less one on the spot. Exactly one of the two must be given."""
    owner_profile_id: Optional[str] = None
    new_owner_profile: Optional[OwnerProfileCreate] = None
    notes: Optional[str] = None
    referred_by: Optional[str] = None

    @model_validator(mode="after")
    def exactly_one_profile_source(self) -> "ClinicOwnerProfileRegistration":
        has_id = self.owner_profile_id is not None
        has_new = self.new_owner_profile is not None

        if has_id == has_new:
            raise ValueError(
                "Provide exactly one of owner_profile_id (to link an existing profile) "
                "or new_owner_profile (to create one)."
            )
        return self