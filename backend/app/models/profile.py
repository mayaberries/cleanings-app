from typing import Optional
from pydantic import EmailStr, HttpUrl

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel


class ProfileBase(CoreModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[HttpUrl] = None


class ProfileCreate(ProfileBase):
    user_id: str


class ProfileUpdate(ProfileBase):
    pass


class ProfileInDB(IDModelMixin, DateTimeModelMixin, ProfileBase):
    user_id: str
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class ProfilePublic(ProfileInDB):
    pass