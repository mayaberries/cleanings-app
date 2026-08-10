"""add is guest to users
Revision ID: 7d8c8ff61169
Revises: 90839ac7b6d8
Create Date: 2026-08-07 17:48:08.668282
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '7d8c8ff61169'
down_revision = '90839ac7b6d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_guest", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_users_is_guest", "users", ["is_guest"])


def downgrade() -> None:
    op.drop_index("ix_users_is_guest", table_name="users")
    op.drop_column("users", "is_guest")
