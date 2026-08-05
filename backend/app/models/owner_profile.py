from typing import Optional
from pydantic import EmailStr, HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class OwnerProfileBase(CoreModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[HttpUrl] = None


class OwnerProfileCreate(OwnerProfileBase):
    user_id: Optional[str] = None


class OwnerProfileUpdate(OwnerProfileBase):
    pass


class OwnerProfileInDB(IDModelMixin, DateTimeModelMixin, OwnerProfileBase):
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class OwnerProfilePublic(OwnerProfileInDB):
    pass
