import datetime
from typing import List

from databases import Database

from app.db.repositories.base import BaseRepository
from app.db.repositories.users import UsersRepository
from app.models.feed import CleaningFeedItem

FETCH_CLEANING_JOBS_FOR_FEED_QUERY = """
    SELECT  id,
            name,
            description,
            price,
            cleaning_type,
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
                    cleaning_type,
                    owner,
                    created_at,
                    updated_at,
                    updated_at as event_timestamp,
                    'is_update' AS event_type
            FROM cleanings
            WHERE updated_at < :starting_date AND updated_at != created_at
            ORDER BY updated_at DESC
            LIMIT :page_chunk_size
        ) UNION (
            SELECT  id,
                    name,
                    description,
                    price,
                    cleaning_type,
                    owner,
                    created_at,
                    updated_at,
                    created_at AS event_timestamp,
                    'is_create' AS event_type
            FROM cleanings
            WHERE created_at < :starting_date
            ORDER BY created_at DESC
            LIMIT :page_chunk_size
        )
    ) AS cleaning_feed
    ORDER BY event_timestamp DESC
    LIMIT :page_chunk_size
"""


class FeedRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.users_repo = UsersRepository(db)

    async def fetch_cleaning_jobs_feed(
            self, *, page_chunk_size: int = 20, starting_date: datetime.datetime,
    ) -> List[CleaningFeedItem]:
        cleaning_feed_item_records = await self.db.fetch_all(
            query=FETCH_CLEANING_JOBS_FOR_FEED_QUERY,
            values={
                "page_chunk_size": page_chunk_size,
                "starting_date": starting_date
            }
        )

        cleaning_feed = [CleaningFeedItem(**f) for f in cleaning_feed_item_records]

        return [await self.populate_cleaning_feed_item(cleaning_feed_item=item) for item in cleaning_feed]

    async def populate_cleaning_feed_item(self, *, cleaning_feed_item: CleaningFeedItem) -> CleaningFeedItem:
        return CleaningFeedItem(
            **cleaning_feed_item.model_dump(exclude={"owner"}),
            owner=await self.users_repo.get_user_by_id(user_id=cleaning_feed_item.owner)
        )