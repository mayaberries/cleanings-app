from enum import Enum
from typing import Optional
from app.models.core import CoreModel, DateTimeModelMixin
from app.models.user import UserPublic
from app.models.cleaning import CleaningPublic


class OfferStatus(str, Enum):
    accepted = "accepted"
    rejected = "rejected"
    pending = "pending"
    cancelled = "cancelled"
    completed = "completed"


class OfferBase(CoreModel):
    user_id: Optional[str] = None
    cleaning_id: Optional[str] = None
    status: Optional[OfferStatus] = OfferStatus.pending


class OfferCreate(OfferBase):
    user_id: str
    cleaning_id: str


class OfferUpdate(CoreModel):
    status: OfferStatus


class OfferInDB(DateTimeModelMixin, OfferBase):
    user_id: str
    cleaning_id: str


class OfferPublic(OfferInDB):
    user: Optional[UserPublic] = None
    cleaning: Optional[CleaningPublic] = None