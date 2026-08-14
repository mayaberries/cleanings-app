"""enforce single superuser

A partial unique index, not just an application-level check -- this is
the actual guarantee that "only one superuser" holds even under a race
(two near-simultaneous bootstrap requests). The app-level count check in
bootstrap_first_superuser is the friendly error path; this is the backstop.

Revision ID: 02702ac5c6e7
Revises: 3a6fb55b8ce9
Create Date: 2026-08-14 15:33:56.038623
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '02702ac5c6e7'
down_revision = '3a6fb55b8ce9'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index(
        "ix_users_single_superuser",
        "users",
        ["is_superuser"],
        unique=True,
        postgresql_where=sa.text("is_superuser = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_single_superuser", table_name="users")