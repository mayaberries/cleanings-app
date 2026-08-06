"""create_clinic_owner_profiles_table

Revision ID: e6c1b48f2a97
Revises: b2e4d1a7f3c6
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'e6c1b48f2a97'
down_revision = 'b2e4d1a7f3c6'
branch_labels = None
depends_on = None


def create_clinic_owner_profiles_table() -> None:
    op.create_table(
        "clinic_owner_profiles",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "clinic_id",
            sa.CHAR(36),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "owner_profile_id",
            sa.CHAR(36),
            sa.ForeignKey("owner_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("status", sa.Text, nullable=False, server_default="active", index=True),
        sa.Column(
            "first_seen_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("referred_by", sa.Text, nullable=True),
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

    op.create_unique_constraint(
        "uq_clinic_owner_profiles_clinic_id_owner_profile_id",
        "clinic_owner_profiles",
        ["clinic_id", "owner_profile_id"],
    )

    op.create_check_constraint(
        "ck_clinic_owner_profiles_status",
        "clinic_owner_profiles",
        "status IN ('active', 'blocked')",
    )

    op.execute(
        """
        CREATE TRIGGER update_clinic_owner_profiles_modtime
            BEFORE UPDATE
            ON clinic_owner_profiles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def upgrade() -> None:
    create_clinic_owner_profiles_table()


def downgrade() -> None:
    op.drop_table("clinic_owner_profiles")