"""add pet id to appointments
Revision ID: b94eca323053
Revises: 7d8c8ff61169
Create Date: 2026-08-10 14:49:24.906344
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'b94eca323053'
down_revision = '7d8c8ff61169'
branch_labels = None
depends_on = None


# TODO deleting a pet that has appointment history shouldn't silently delete the appointments
# ondelete="RESTRICT" deliberately blocks it. Think if a better approach is a soft delete instead
def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column(
            "pet_id",
            sa.CHAR(36),
            sa.ForeignKey("pet_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_index("ix_appointments_pet_id", "appointments", ["pet_id"])


def downgrade() -> None:
    op.drop_index("ix_appointments_pet_id", table_name="appointments")
    op.drop_column("appointments", "pet_id")
