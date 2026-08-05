from typing import List
import datetime
from collections import Counter
import pytest

from httpx import AsyncClient
from fastapi import FastAPI, status

from app.models.service import ServiceInDB

pytestmark = pytest.mark.asyncio


class TestServiceFeed:
    @pytest.mark.skip(
        reason="Feed's future is undecided post-pivot away from marketplace discovery "
               "toward scheduling + notifications. See roadmap. Revisit before deleting "
               "or fixing."
    )
    async def test_service_feed_returns_valid_response(
            self,
            *,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_list_of_new_and_updated_services: List[ServiceInDB]
    ) -> None:
        service_ids = [
            service.id for service in test_list_of_new_and_updated_services]

        response = await clinic_a_admin_client.get(
            app.url_path_for("feed:get-service-feed-for-user")
        )

        assert response.status_code == status.HTTP_200_OK

        service_feed = response.json()

        assert isinstance(service_feed, list)
        assert len(service_feed) == 20
        assert set(feed_item["id"] for feed_item in service_feed).issubset(
            set(service_ids))

    @pytest.mark.skip(
        reason="Feed's future is undecided post-pivot away from marketplace discovery "
               "toward scheduling + notifications. See roadmap. Revisit before deleting "
               "or fixing."
    )
    async def test_service_fed_response_is_ordered_correctly(
            self,
            *,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_list_of_new_and_updated_services: List[ServiceInDB]
    ) -> None:
        response = await clinic_a_admin_client.get(app.url_path_for("feed:get-service-feed-for-user"))

        assert response.status_code == status.HTTP_200_OK
        service_feed = response.json()

        for feed_item in service_feed[:13]:
            assert feed_item["event_type"] == "is_update"
        for feed_item in service_feed[13:]:
            assert feed_item["event_type"] == "is_create"

    @pytest.mark.skip(
        reason="Feed's future is undecided post-pivot away from marketplace discovery "
               "toward scheduling + notifications. See roadmap. Revisit before deleting "
               "or fixing."
    )
    async def test_service_feed_can_paginate_correctly(
            self,
            *,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_list_of_new_and_updated_services: List[ServiceInDB],
    ) -> None:
        starting_date = datetime.datetime.now() + datetime.timedelta(minutes=10)

        combos = []
        for chunk_size in [25, 15, 10]:
            response = await clinic_a_admin_client.get(
                app.url_path_for("feed:get-service-feed-for-user"),
                params={"starting_date": starting_date, "page_chunk_size": chunk_size}
            )

            assert response.status_code == status.HTTP_200_OK

            page_json = response.json()
            assert len(page_json) == chunk_size

            id_and_event_combo = set(f"{item['id']}-{item['event_type']}" for item in page_json)
            combos.append(id_and_event_combo)
            starting_date = page_json[-1]["event_timestamp"]

        length_of_all_id_combos = sum(len(combo) for combo in combos)
        assert len(set().union(*combos)) == length_of_all_id_combos

    @pytest.mark.skip(
        reason="Feed's future is undecided post-pivot away from marketplace discovery "
               "toward scheduling + notifications. See roadmap. Revisit before deleting "
               "or fixing."
    )
    async def test_service_feed_has_created_and_updated_items_for_modified_service_jobs(
            self,
            *,
            app: FastAPI,
            clinic_a_admin_client: AsyncClient,
            test_list_of_new_and_updated_services: List[ServiceInDB]
    ) -> None:
        res_page_1 = await clinic_a_admin_client.get(
            app.url_path_for("feed:get-service-feed-for-user"),
            params={"page_chunk_size": 30},
        )
        assert res_page_1.status_code == status.HTTP_200_OK
        ids_page_1 = [feed_item["id"] for feed_item in res_page_1.json()]

        new_starting_date = res_page_1.json()[-1]["event_timestamp"]

        res_page_2 = await clinic_a_admin_client.get(
            app.url_path_for("feed:get-service-feed-for-user"),
            params={"starting_date": new_starting_date, "page_chunk_size": 33}
        )
        assert res_page_2.status_code == status.HTTP_200_OK
        ids_page_2 = [feed_item["id"] for feed_item in res_page_2.json()]

        id_counts = Counter(ids_page_1 + ids_page_2)
        assert len([id for id, cnt in id_counts.items() if cnt > 1]) == 13
