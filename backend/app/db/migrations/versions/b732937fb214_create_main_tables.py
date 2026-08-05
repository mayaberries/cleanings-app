"""create_main_tables
Revision ID: b732937fb214
Revises: 
Create Date: 2021-11-23 18:09:17.722455
"""
from typing import Tuple
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'b732937fb214'
down_revision = None
branch_labels = None
depends_on = None


def create_updated_at_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=indexed,
        ),
    )


def create_clinics_table() -> None:
    op.create_table(
        "clinics",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("name", sa.Text, nullable=False, index=True),
        sa.Column("email", sa.Text, nullable=True),
        sa.Column("phone_number", sa.Text, nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_clinics_modtime
            BEFORE UPDATE
            ON clinics
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_services_table() -> None:
    op.create_table(
        "services",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("name", sa.Text, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.Text, nullable=False, index=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("clinic_id", sa.CHAR(36), sa.ForeignKey(
            "clinics.id", ondelete="CASCADE"), nullable=False),
        *timestamps(),
    )

    op.execute(
        """
        CREATE TRIGGER update_services_modtime
            BEFORE UPDATE
            ON services
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_users_table() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("username", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email", sa.Text, unique=True, nullable=False, index=True),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="False"),
        sa.Column("role", sa.Text, nullable=False, server_default="client", index=True),
        sa.Column("clinic_id", sa.CHAR(36), sa.ForeignKey("clinics.id", ondelete="SET NULL"), nullable=True,
                  index=True),
        sa.Column("salt", sa.Text, nullable=False),
        sa.Column("password", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="True"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="False"),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_user_modtime
            BEFORE UPDATE
            ON users
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_owner_profiles_table() -> None:
    op.create_table(
        "owner_profiles",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("full_name", sa.Text, nullable=True),
        sa.Column("phone_number", sa.Text, nullable=True),
        sa.Column("bio", sa.Text, nullable=True, server_default=""),
        sa.Column("image", sa.Text, nullable=True),
        sa.Column("user_id", sa.CHAR(36), sa.ForeignKey(
            "users.id", ondelete="CASCADE")),
        *timestamps(),
    )
    op.execute(
        """
        CREATE TRIGGER update_owner_profiles_modtime
            BEFORE UPDATE
            ON owner_profiles
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_appointments_table() -> None:
    op.create_table(
        "appointments",
        sa.Column(
            "user_id",  # 'user' is a reserved word in postgres, so going with user_id instead
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "service_id",  # going with `service_id` for consistency
            sa.CHAR(36),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.Text, nullable=False,
                  server_default="requested", index=True),
        *timestamps(),
    )
    op.create_primary_key("pk_appointments",
                          "appointments", ["user_id", "service_id"])
    op.execute(
        """
        CREATE TRIGGER update_appointments_modtime
            BEFORE UPDATE
            ON appointments
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_cleaner_evaluations_table() -> None:
    op.create_table(
        "service_to_cleaner_evaluations",
        sa.Column(
            "service_id",  # job that was completed
            sa.CHAR(36),
            sa.ForeignKey("services.id", ondelete="SET NULL"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "cleaner_id",  # user who completed the job
            sa.CHAR(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
            index=True,
        ),
        sa.Column("no_show", sa.Boolean, nullable=False,
                  server_default="False"),
        sa.Column("headline", sa.Text, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("professionalism", sa.Integer, nullable=True),
        sa.Column("completeness", sa.Integer, nullable=True),
        sa.Column("efficiency", sa.Integer, nullable=True),
        sa.Column("overall_rating", sa.Integer, nullable=False),
        *timestamps(),
    )
    op.create_primary_key(
        "pk_service_to_cleaner_evaluations", "service_to_cleaner_evaluations", [
            "service_id", "cleaner_id"]
    )
    op.execute(
        """
        CREATE TRIGGER update_service_to_cleaner_evaluations_modtime
            BEFORE UPDATE
            ON service_to_cleaner_evaluations
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )


def create_pet_profiles_table() -> None:
    op.create_table(
        "pet_profiles",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("species", sa.Text, nullable=True),
        sa.Column("breed", sa.Text, nullable=True),
        sa.Column("birth_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("image", sa.Text, nullable=True),
        sa.Column("owner", sa.CHAR(36), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        *timestamps(),
    )
    op.execute("""
            CREATE TRIGGER update_pet_profiles_modtime
                BEFORE UPDATE ON pet_profiles
                FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        """)


def upgrade() -> None:
    create_updated_at_trigger()
    create_clinics_table()
    create_users_table()
    create_owner_profiles_table()
    create_services_table()
    create_appointments_table()
    create_cleaner_evaluations_table()
    create_pet_profiles_table()


def downgrade() -> None:
    op.drop_table("pets")
    op.drop_table("service_to_cleaner_evaluations")
    op.drop_table("appointments")
    op.drop_table("services")
    op.drop_table("profiles")
    op.drop_table("users")
    op.drop_table("clinics")
    op.execute("DROP FUNCTION update_updated_at_column")
