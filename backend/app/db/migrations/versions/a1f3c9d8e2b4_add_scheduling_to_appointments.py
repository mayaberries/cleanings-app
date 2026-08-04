"""add_scheduling_to_appointments

Revision ID: a1f3c9d8e2b4
Revises: b732937fb214
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1f3c9d8e2b4'
down_revision = 'b732937fb214'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Surrogate id, nullable at first so we can backfill existing rows
    op.add_column("appointments", sa.Column("id", sa.CHAR(36), nullable=True))

    connection = op.get_bind()
    # requires pgcrypto (`CREATE EXTENSION IF NOT EXISTS pgcrypto;`) for gen_random_uuid()
    connection.execute(sa.text(
        "UPDATE appointments SET id = gen_random_uuid()::text WHERE id IS NULL"
    ))
    op.alter_column("appointments", "id", nullable=False)

    # 2. Scheduling columns. No existing row has a real time, so backfill to
    #    created_at + a default duration purely so NOT NULL can be enforced —
    #    these placeholder values are not meaningful and should be reviewed
    #    if this ever runs against real production data.
    op.add_column("appointments", sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True))
    connection.execute(sa.text("""
        UPDATE appointments
        SET start_time = created_at,
            end_time = created_at + interval '30 minutes'
        WHERE start_time IS NULL
    """))
    op.alter_column("appointments", "start_time", nullable=False)
    op.alter_column("appointments", "end_time", nullable=False)

    # 3. Swap PK: (user_id, service_id) -> id. This is what allows the same
    #    user to book the same service more than once.
    op.drop_constraint("pk_appointments", "appointments", type_="primary")
    op.create_primary_key("pk_appointments", "appointments", ["id"])

    # 4. Support overlap-checking queries
    op.create_index("ix_appointments_service_id_start_time", "appointments", ["service_id", "start_time"])
    op.create_index("ix_services_owner", "services", ["owner"])


def downgrade() -> None:
    op.drop_index("ix_services_owner", table_name="services")
    op.drop_index("ix_appointments_service_id_start_time", table_name="appointments")
    op.drop_constraint("pk_appointments", "appointments", type_="primary")
    op.create_primary_key("pk_appointments", "appointments", ["user_id", "service_id"])
    op.drop_column("appointments", "end_time")
    op.drop_column("appointments", "start_time")
    op.drop_column("appointments", "id")