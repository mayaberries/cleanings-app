"""create_clinic_availability_table
Revision ID: a26a66e8e83f
Revises: b94eca323053
Create Date: 2026-08-10 16:14:58.341576
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision = 'a26a66e8e83f'
down_revision = 'b94eca323053'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinic_availability",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "clinic_id",
            sa.CHAR(36),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Weekly recurring hours, keyed by lowercase weekday name, e.g.
        # {"monday": [{"start": "09:00:00", "end": "17:00:00"}], ...}.
        # JSONB rather than a slots-per-row table on purpose -- this is a
        # handful of ranges per day, read and replaced as one blob via
        # GET/PUT, not queried per-row or per-slot. See PR description for
        # the full reasoning; the short version is this data's access
        # pattern doesn't earn a join.
        sa.Column("schedule", JSONB, nullable=False, server_default="{}"),
        sa.Column("timezone", sa.Text, nullable=False, server_default="UTC"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # One-to-one with clinics -- also what the repository's
    # ON CONFLICT (clinic_id) upsert relies on.
    op.create_unique_constraint(
        "uq_clinic_availability_clinic_id", "clinic_availability", ["clinic_id"]
    )

    # Reuses the trigger function created in b732937fb214_create_main_tables.py.
    op.execute(
        """
        CREATE TRIGGER update_clinic_availability_modtime
            BEFORE UPDATE
            ON clinic_availability
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def downgrade() -> None:
    op.drop_table("clinic_availability")
