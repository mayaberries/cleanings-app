"""add clinic slug
Revision ID: 3a6fb55b8ce9
Revises: a26a66e8e83f
Create Date: 2026-08-14 15:12:15.958941
"""
import re
import unicodedata

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '3a6fb55b8ce9'
down_revision = 'a26a66e8e83f'
branch_labels = None
depends_on = None


def _slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)


def upgrade() -> None:
    op.add_column("clinics", sa.Column("slug", sa.Text, nullable=True))

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, name FROM clinics")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE clinics SET slug = :slug WHERE id = :id"),
            {"slug": _slugify(row.name), "id": row.id},
        )

    op.alter_column("clinics", "slug", nullable=False)
    op.create_unique_constraint("uq_clinics_slug", "clinics", ["slug"])
    op.create_index("ix_clinics_slug", "clinics", ["slug"])


def downgrade() -> None:
    op.drop_index("ix_clinics_slug", table_name="clinics")
    op.drop_constraint("uq_clinics_slug", "clinics", type_="unique")
    op.drop_column("clinics", "slug")
