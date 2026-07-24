"""mapa mundial: entradas automáticas derivadas de los viajes

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("world_places", sa.Column("auto", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("world_places", sa.Column("hidden", sa.Boolean(), nullable=False, server_default="0"))
    op.add_column("world_places", sa.Column("origin", sa.String(200), nullable=True))
    with op.batch_alter_table("world_places") as batch:
        batch.add_column(sa.Column("trip_place_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_world_places_trip_place_id", "places", ["trip_place_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
