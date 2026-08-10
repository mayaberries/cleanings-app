from typing import List
import datetime
from fastapi import APIRouter, Depends, Query
from app.models.appointments.feed import ServiceFeedItem
from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.database import get_repository
from app.db.repositories.feed import FeedRepository


router = APIRouter()


@router.get(
    "/services/",
    response_model=List[ServiceFeedItem],
    name="feed:get-service-feed-for-user",
    dependencies=[Depends(get_current_active_user)]
)
async def get_service_feed_for_user(
    page_chunk_size: int = Query(
        20,
        ge=1,
        le=50,
        description="Used to determine how many service feed item objects to return in the response."
    ),
    starting_date: datetime.datetime = Query(
        datetime.datetime.now() + datetime.timedelta(minutes=10),
        description="Used to determine the timestamp at which to begin querying for service feed items."
    ),
    feed_repository: FeedRepository = Depends(get_repository(FeedRepository))
) -> List[ServiceFeedItem]:
    return await feed_repository.fetch_service_jobs_feed(
        starting_date=starting_date, page_chunk_size=page_chunk_size,
    )
