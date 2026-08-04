"""rekey_evaluations_by_appointment

Revision ID: b2e4d1a7f3c6
Revises: a1f3c9d8e2b4
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2e4d1a7f3c6'
down_revision = 'a1f3c9d8e2b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "service_to_cleaner_evaluations",
        sa.Column("appointment_id", sa.CHAR(36), sa.ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True),
    )
    # No production data predates this migration in this project, so there's
    # nothing to backfill. If that's ever not true, appointment_id must be
    # populated manually before the NOT NULL/PK swap below.
    op.drop_constraint("pk_service_to_cleaner_evaluations", "service_to_cleaner_evaluations", type_="primary")
    op.alter_column("service_to_cleaner_evaluations", "appointment_id", nullable=False)
    op.create_primary_key("pk_service_to_cleaner_evaluations", "service_to_cleaner_evaluations", ["appointment_id"])
    op.create_index("ix_evaluations_cleaner_id", "service_to_cleaner_evaluations", ["cleaner_id"])
    op.create_index("ix_evaluations_service_id", "service_to_cleaner_evaluations", ["service_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluations_service_id", table_name="service_to_cleaner_evaluations")
    op.drop_index("ix_evaluations_cleaner_id", table_name="service_to_cleaner_evaluations")
    op.drop_constraint("pk_service_to_cleaner_evaluations", "service_to_cleaner_evaluations", type_="primary")
    op.create_primary_key(
        "pk_service_to_cleaner_evaluations", "service_to_cleaner_evaluations", ["service_id", "cleaner_id"]
    )
    op.drop_column("service_to_cleaner_evaluations", "appointment_id")