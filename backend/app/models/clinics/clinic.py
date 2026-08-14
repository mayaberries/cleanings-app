import re
import unicodedata
from typing import Optional

from pydantic import field_validator

from app.models.core import IDModelMixin, CoreModel, DateTimeModelMixin


def slugify(value: str) -> str:
    """Shared with the slug backfill migration (f1a2b3c4d5e6) — keep the
    two in sync if this ever changes, since the migration can't import
    application code."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


class ClinicBase(CoreModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None


class ClinicCreate(ClinicBase):
    name: str
    slug: Optional[str] = None

    @field_validator("slug")
    @classmethod
    def slug_is_valid(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = slugify(value)
        if not normalized:
            raise ValueError("slug must contain at least one alphanumeric character")
        return normalized


class ClinicUpdate(ClinicBase):
    pass


class ClinicInDB(IDModelMixin, DateTimeModelMixin, ClinicBase):
    name: str
    slug: str


class ClinicPublic(IDModelMixin, DateTimeModelMixin, ClinicBase):
    name: str
    slug: str
