"""multi-usuario: users, sessions, families y scoping por familia

Revision ID: 0a762ed5e21d
Revises: 52b29335337b
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0a762ed5e21d"
down_revision: Union[str, None] = "52b29335337b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# convención para poder soltar las uniques anónimas al recrear tablas (batch mode)
NAMING = {"uq": "uq_%(table_name)s_%(column_0_name)s"}

# tablas que pasan a llevar family_id
FAMILY_TABLES = ("travelers", "trips", "categories", "packing_templates", "world_places")


def upgrade() -> None:
    # --- tablas nuevas ---
    op.create_table(
        "families",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "traveler_id",
            sa.Integer(),
            sa.ForeignKey("travelers.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("theme", sa.String(10), nullable=False, server_default="system"),
        sa.Column("language", sa.String(5), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    # --- columnas family_id (nullable de inicio para poder backfillear) ---
    with op.batch_alter_table("travelers") as batch_op:
        batch_op.add_column(sa.Column("family_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("avatar_image", sa.String(100), nullable=True))
        batch_op.create_foreign_key(
            "fk_travelers_family_id_families", "families", ["family_id"], ["id"], ondelete="RESTRICT"
        )
    with op.batch_alter_table("trips") as batch_op:
        batch_op.add_column(sa.Column("family_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_trips_family_id_families", "families", ["family_id"], ["id"], ondelete="SET NULL"
        )
    with op.batch_alter_table("categories", naming_convention=NAMING) as batch_op:
        batch_op.add_column(sa.Column("family_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_categories_family_id_families", "families", ["family_id"], ["id"], ondelete="CASCADE"
        )
    with op.batch_alter_table("packing_templates", naming_convention=NAMING) as batch_op:
        batch_op.add_column(sa.Column("family_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_packing_templates_family_id_families", "families", ["family_id"], ["id"], ondelete="CASCADE"
        )
    with op.batch_alter_table("world_places") as batch_op:
        batch_op.add_column(sa.Column("family_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_world_places_family_id_families", "families", ["family_id"], ["id"], ondelete="CASCADE"
        )

    # --- backfill: una instancia con datos pasa a tener una familia por defecto ---
    # (el bootstrap del primer admin reutiliza esta familia en vez de crear otra)
    conn = op.get_bind()
    has_rows = any(
        conn.execute(sa.text(f"SELECT 1 FROM {table} LIMIT 1")).first() is not None
        for table in FAMILY_TABLES
    )
    if has_rows:
        result = conn.execute(sa.text("INSERT INTO families (name) VALUES ('Familia')"))
        fam_id = result.lastrowid
        for table in FAMILY_TABLES:
            conn.execute(
                sa.text(f"UPDATE {table} SET family_id = :fam"), {"fam": fam_id}
            )

    # --- NOT NULL + swap de uniques globales → por familia ---
    with op.batch_alter_table("categories", naming_convention=NAMING) as batch_op:
        batch_op.alter_column("family_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_constraint("uq_categories_kind", type_="unique")
        batch_op.create_unique_constraint(
            "uq_categories_family_kind_name", ["family_id", "kind", "name"]
        )
    with op.batch_alter_table("packing_templates", naming_convention=NAMING) as batch_op:
        batch_op.alter_column("family_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_constraint("uq_packing_templates_name", type_="unique")
        batch_op.create_unique_constraint(
            "uq_packing_templates_family_name", ["family_id", "name"]
        )
    with op.batch_alter_table("world_places") as batch_op:
        batch_op.alter_column("family_id", existing_type=sa.Integer(), nullable=False)
        batch_op.create_index("ix_world_places_family_id", ["family_id"])

    # la lista de viajes filtra por viajero en cada carga de la home
    op.create_index("ix_trip_travelers_traveler_id", "trip_travelers", ["traveler_id"])


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
