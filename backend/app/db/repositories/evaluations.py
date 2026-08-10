from typing import List, Optional
from databases.core import Database
from app.db.repositories.base import BaseRepository
from app.db.repositories.appointments import AppointmentsRepository
from app.models.appointments.appointment import AppointmentInDB
from app.models.appointments.evaluation import EvaluationAggregate, EvaluationCreate, EvaluationInDB
from app.models.auth.user import UserInDB

CREATE_EVALUATION_FOR_APPOINTMENT_QUERY = """
    INSERT INTO service_to_cleaner_evaluations (
        appointment_id,
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
        :appointment_id,
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
    RETURNING appointment_id,
              service_id,
              cleaner_id,
              no_show,
              headline,
              comment,
              professionalism,
              completeness,
              efficiency,
              overall_rating,
              created_at,
              updated_at;
"""

GET_EVALUATION_FOR_APPOINTMENT_QUERY = """
    SELECT appointment_id, service_id, cleaner_id, no_show, headline, comment,
           professionalism, completeness, efficiency, overall_rating, created_at, updated_at
    FROM service_to_cleaner_evaluations
    WHERE appointment_id = :appointment_id;
"""

LIST_EVALUATIONS_FOR_CLEANER_QUERY = """
    SELECT appointment_id, service_id, cleaner_id, no_show, headline, comment,
           professionalism, completeness, efficiency, overall_rating, created_at, updated_at
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
        COUNT(appointment_id) AS total_evaluations,
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
        self.appointments_repo = AppointmentsRepository(db)

    async def create_evaluation_for_appointment(
            self, *, evaluation_create: EvaluationCreate, appointment: AppointmentInDB
    ) -> EvaluationInDB:
        async with self.db.transaction():
            created_eval = await self.db.fetch_one(
                query=CREATE_EVALUATION_FOR_APPOINTMENT_QUERY,
                values={
                    **evaluation_create.model_dump(),
                    "appointment_id": appointment.id,
                    "service_id": appointment.service_id,
                    "cleaner_id": appointment.user_id,
                }
            )

            await self.appointments_repo.mark_as_completed(appointment=appointment)

            return EvaluationInDB(**created_eval)

    async def list_evaluations_for_cleaner(self, *, cleaner: UserInDB) -> List[EvaluationInDB]:
        evaluations = await self.db.fetch_all(
            query=LIST_EVALUATIONS_FOR_CLEANER_QUERY,
            values={"cleaner_id": cleaner.id}
        )
        return [EvaluationInDB(**e) for e in evaluations]

    async def get_evaluation_for_appointment(self, *, appointment_id: str) -> Optional[EvaluationInDB]:
        evaluation = await self.db.fetch_one(
            query=GET_EVALUATION_FOR_APPOINTMENT_QUERY,
            values={"appointment_id": appointment_id}
        )
        if not evaluation:
            return None
        return EvaluationInDB(**evaluation)

    async def get_cleaner_aggregates(self, *, cleaner: UserInDB) -> EvaluationAggregate:
        return await self.db.fetch_one(
            query=GET_CLEANER_AGGREGATE_RATINGS_QUERY,
            values={"cleaner_id": cleaner.id}
        )