from typing import List
from databases.core import Database
from app.db.repositories.base import BaseRepository
from app.db.repositories.appointments import AppointmentsRepository
from app.models.service import ServiceInDB
from app.models.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB
from app.models.user import UserInDB

CREATE_OWNER_EVALUATION_FOR_CLEANER_QUERY = """
    INSERT INTO service_to_cleaner_evaluations (
        service_id,
        cleaner_id,
        no_show,
        headline,
        comment,
        professionalism,
        completeness,
        efficiency,
        overall_rating
    )
    VALUES (
        :service_id,
        :cleaner_id,
        :no_show,
        :headline,
        :comment,
        :professionalism,
        :completeness,
        :efficiency,
        :overall_rating
    )
    RETURNING no_show,
              service_id,
              cleaner_id,
              headline,
              comment,
              professionalism,
              completeness,
              efficiency,
              overall_rating,
              created_at,
              updated_at;
"""

GET_CLEANER_EVALUATION_FOR_SERVICE_QUERY = """
    SELECT no_show,
           service_id,
           cleaner_id,
           headline,
           comment,
           professionalism,
           completeness,
           efficiency,
           overall_rating,
           created_at,
           updated_at
    FROM service_to_cleaner_evaluations
    WHERE service_id = :service_id AND cleaner_id = :cleaner_id;
"""
LIST_EVALUATIONS_FOR_CLEANER_QUERY = """
    SELECT no_show,
           service_id,
           cleaner_id,
           headline,
           comment,
           professionalism,
           completeness,
           efficiency,
           overall_rating,
           created_at,
           updated_at
    FROM service_to_cleaner_evaluations
    WHERE cleaner_id = :cleaner_id;
"""
GET_CLEANER_AGGREGATE_RATINGS_QUERY = """
    SELECT        
        AVG(professionalism) AS avg_professionalism,
        AVG(completeness)    AS avg_completeness,
        AVG(efficiency)      AS avg_efficiency,
        AVG(overall_rating)  AS avg_overall_rating,
        MIN(overall_rating)  AS min_overall_rating,
        MAX(overall_rating)  AS max_overall_rating,
        COUNT(service_id)   AS total_evaluations,
        SUM(no_show::int)    AS total_no_show,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 1) AS one_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 2) AS two_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 3) AS three_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 4) AS four_stars,
        COUNT(overall_rating) FILTER(WHERE overall_rating = 5) AS five_stars
    FROM service_to_cleaner_evaluations
    WHERE cleaner_id = :cleaner_id;
"""


class EvaluationsRepository(BaseRepository):
    def __init__(self, db: Database) -> None:
        super().__init__(db)
        self.offers_repo = AppointmentsRepository(db)

    async def create_evaluation_for_cleaner(
            self, *, evaluation_create: EvaluationCreate, cleaner: ServiceInDB, service: UserInDB
    ) -> EvaluationInDB:
        async with self.db.transaction():
            created_eval = await self.db.fetch_one(
                query=CREATE_OWNER_EVALUATION_FOR_CLEANER_QUERY,
                values={
                    **evaluation_create.model_dump(),
                    "service_id": service.id,
                    "cleaner_id": cleaner.id
                }
            )

            await self.offers_repo.mark_as_completed(
                service=service,
                cleaner=cleaner
            )

            return EvaluationInDB(**created_eval)

    async def list_evaluations_for_cleaner(
            self, *, cleaner: UserInDB
    ) -> List[EvaluationInDB]:
        evaluations = await self.db.fetch_all(
            query=LIST_EVALUATIONS_FOR_CLEANER_QUERY,
            values={"cleaner_id": cleaner.id}
        )

        return [EvaluationInDB(**e) for e in evaluations]

    async def get_cleaner_evaluation_for_service(
            self, *, service: ServiceInDB, cleaner: UserInDB
    ) -> EvaluationInDB:
        evaluation = await self.db.fetch_one(
            query=GET_CLEANER_EVALUATION_FOR_SERVICE_QUERY,
            values={"service_id": service.id, "cleaner_id": cleaner.id}
        )

        if not evaluation:
            return None

        return EvaluationInDB(**evaluation)

    async def get_cleaner_aggregates(
            self, *, cleaner: UserInDB
    ) -> EvaluationAggregate:
        return await self.db.fetch_one(
            query=GET_CLEANER_AGGREGATE_RATINGS_QUERY,
            values={"cleaner_id": cleaner.id}
        )
