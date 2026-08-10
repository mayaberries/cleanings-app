import datetime
from typing import List

from databases import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.appointments.feed import ServiceFeedItem

FETCH_SERVICE_JOBS_FOR_FEED_QUERY = """
    SELECT  id,
            name,
            description,
            price,
            category,
            owner,
            created_at,
            updated_at,
            event_type,
            event_timestamp,
            ROW_NUMBER() OVER ( ORDER BY event_timestamp DESC ) AS row_number
    FROM (
        (
            SELECT  id,
                    name,
                    description,
                    price,
                    category,
                    owner,
                    created_at,
                    updated_at,
                    updated_at as event_timestamp,
                    'is_update' AS event_type
            FROM services
            WHERE updated_at < :starting_date AND updated_at != created_at
            ORDER BY updated_at DESC
            LIMIT :page_chunk_size
        ) UNION (
            SELECT  id,
                    name,
                    description,
                    price,
                    category,
                    owner,
                    created_at,
                    updated_at,
                    created_at AS event_timestamp,
                    'is_create' AS event_type
            FROM services
            WHERE created_at < :starting_date
            ORDER BY created_at DESC
            LIMIT :page_chunk_size
        )
    ) AS service_feed
    ORDER BY event_timestamp DESC
    LIMIT :page_chunk_size
"""


class FeedRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def fetch_service_jobs_feed(
            self, *, page_chunk_size: int = 20, starting_date: datetime.datetime,
    ) -> List[ServiceFeedItem]:
        service_feed_item_records = await self.db.fetch_all(
            query=FETCH_SERVICE_JOBS_FOR_FEED_QUERY,
            values={
                "page_chunk_size": page_chunk_size,
                "starting_date": starting_date
            }
        )

        service_feed = [ServiceFeedItem(**f) for f in service_feed_item_records]

        return [await self.populate_service_feed_item(service_feed_item=item) for item in service_feed]

    async def populate_service_feed_item(self, *, service_feed_item: ServiceFeedItem) -> ServiceFeedItem:
        return ServiceFeedItem(
            **service_feed_item.model_dump(exclude={"owner"}),
            owner=await self.users_repo.get_user_by_id(user_id=service_feed_item.owner)
        )