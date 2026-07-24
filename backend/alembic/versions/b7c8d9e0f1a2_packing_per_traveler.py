"""maletas por viajero: traveler_id en packing_items + selección de plantilla

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # los elementos existentes quedan en la maleta común (traveler_id NULL)
    # batch mode con FK nombrada: SQLite requiere reconstruir la tabla para añadir la constraint
    with op.batch_alter_table("packing_items") as batch:
        batch.add_column(sa.Column("traveler_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_packing_items_traveler_id",
            "travelers",
            ["traveler_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "packing_selections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("traveler_id", sa.Integer(), sa.ForeignKey("travelers.id", ondelete="CASCADE"), nullable=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("packing_templates.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_packing_selections_trip_id", "packing_selections", ["trip_id"])


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
