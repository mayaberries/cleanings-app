from datetime import datetime
from enum import Enum
from typing import Optional

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin


class ClinicKeyEnvironment(str, Enum):
    live = "live"
    test = "test"


class ClinicAPIKeyBase(CoreModel):
    label: Optional[str] = None
    environment: ClinicKeyEnvironment = ClinicKeyEnvironment.live


class ClinicAPIKeyCreate(ClinicAPIKeyBase):
    pass


class ClinicAPIKeyInDB(IDModelMixin, DateTimeModelMixin, ClinicAPIKeyBase):
    clinic_id: str
    public_key: str
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


class ClinicAPIKeyPublic(IDModelMixin, DateTimeModelMixin, ClinicAPIKeyBase):
    """
    Deliberately includes the full `public_key`, not a masked version.
    Unlike a secret key, this value isn't sensitive — the clinic admin can
    look it up any time to re-paste into their embed. What matters for
    security is that only clinic-admin-authenticated (JWT) requests can
    reach this model at all; the key itself relies on route scoping and
    rate limiting once it's in the wild, not on being hidden here.
    """
    clinic_id: str
    public_key: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None