"""orden manual de familias (drag & drop)

Revision ID: caf68993213e
Revises: 0a762ed5e21d
Create Date: 2026-07-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "caf68993213e"
down_revision: Union[str, None] = "0a762ed5e21d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("families") as batch_op:
        batch_op.add_column(
            sa.Column("position", sa.Integer(), nullable=False, server_default="0")
        )
    # posiciones iniciales estables: el orden alfabético que se veía hasta ahora
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM families ORDER BY name")).fetchall()
    for position, row in enumerate(rows):
        conn.execute(
            sa.text("UPDATE families SET position = :pos WHERE id = :id"),
            {"pos": position, "id": row.id},
        )


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
