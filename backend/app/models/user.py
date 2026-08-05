import string
from enum import Enum
from typing import Optional
from pydantic import EmailStr, constr, field_validator

from app.models.core import DateTimeModelMixin, IDModelMixin, CoreModel
from app.models.token import AccessToken
from app.models.owner_profile import OwnerProfilePublic


def validate_username(username: str) -> str:
    allowed = string.ascii_letters + string.digits + "-" + "_"
    assert all(char in allowed for char in username), "Invalid characters in username."
    assert len(username) >= 3, "Username must be 3 in characters or more."
    return username


class UserRole(str, Enum):
    clinic_admin = "clinic_admin"
    clinic_aux = "clinic_aux"
    client = "client"


class UserBase(CoreModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    email_verified: bool = False
    role: UserRole = UserRole.client
    clinic_id: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(CoreModel):
    email: EmailStr
    password: constr(min_length=7, max_length=100)
    username: str

    @field_validator("username", mode="before")
    @classmethod
    def username_is_valid(cls, username: str) -> str:
        return validate_username(username)


class UserUpdate(CoreModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None

    @field_validator("username", mode="before")
    @classmethod
    def username_is_valid(cls, username: str) -> str:
        return validate_username(username)


class UserPasswordUpdate(CoreModel):
    password: constr(min_length=7, max_length=100)
    salt: str


class UserInDB(IDModelMixin, DateTimeModelMixin, UserBase):
    password: constr(min_length=7, max_length=100)
    salt: str


class UserPublic(IDModelMixin, DateTimeModelMixin, UserBase):
    access_token: Optional[AccessToken] = None
    profile: Optional[OwnerProfilePublic] = None
