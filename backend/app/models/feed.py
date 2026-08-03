from typing import Optional, Literal
import datetime
from app.models.core import CoreModel
from app.models.service import ServicePublic


class FeedItem(CoreModel):
    row_number: Optional[int] = None
    event_timestamp: Optional[datetime.datetime] = None


class ServiceFeedItem(ServicePublic, FeedItem):
    event_type: Optional[Literal["is_update", "is_create"]] = None