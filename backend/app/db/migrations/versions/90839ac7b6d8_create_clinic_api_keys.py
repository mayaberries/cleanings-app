"""create clinic api keys

Public/embeddable booking widget auth: a clinic-scoped, Stripe-publishable-
-key-style credential. Unlike the JWT/user password stack, this value is
NOT a secret — it's a lookup key, not stored hashed, and is safe to ship in
client-side JS on a clinic's own website. The security boundary is route
scoping (only public booking-surface routes accept it) plus rate limiting,
not concealment. See app/api/dependencies/public_auth.py.

A clinic may hold several keys at once so a leaked/rotated key can be
revoked without any embed downtime.

Revision ID: 90839ac7b6d8
Revises: e6c1b48f2a97
Create Date: 2026-08-06 11:48:25.675962
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '90839ac7b6d8'
down_revision = 'e6c1b48f2a97'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinic_api_keys",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column(
            "clinic_id",
            sa.CHAR(36),
            sa.ForeignKey("clinics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Not hashed on purpose — this is a publishable-style key, safe to
        # display back to the clinic admin any time. Uniqueness is what the
        # public-auth lookup relies on for speed.
        sa.Column("public_key", sa.Text, nullable=False, unique=True),
        sa.Column("environment", sa.Text, nullable=False, server_default="live"),
        sa.Column("label", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.CheckConstraint("environment IN ('live', 'test')", name="ck_clinic_api_keys_environment"),
    )

    # Hot-path lookup: get_active_clinic_by_public_key() filters on exactly
    # these three columns on every public-surface request.
    op.create_index(
        "ix_clinic_api_keys_public_key_active",
        "clinic_api_keys",
        ["public_key"],
        postgresql_where=sa.text("is_active = true AND revoked_at IS NULL"),
    )
    op.create_index("ix_clinic_api_keys_clinic_id", "clinic_api_keys", ["clinic_id"])

    # Reuses the update_updated_at_column() trigger function created in
    # b732937fb214_create_main_tables.py.
    op.execute(
        """
        CREATE TRIGGER update_clinic_api_keys_modtime
            BEFORE UPDATE
            ON clinic_api_keys
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_clinic_api_keys_modtime ON clinic_api_keys;")
    op.drop_index("ix_clinic_api_keys_clinic_id", table_name="clinic_api_keys")
    op.drop_index("ix_clinic_api_keys_public_key_active", table_name="clinic_api_keys")
    op.drop_table("clinic_api_keys")
