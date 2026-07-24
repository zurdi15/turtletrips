"""gastos enlazados a sitios: expenses.place_id

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("expenses") as batch:
        batch.add_column(sa.Column("place_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_expenses_place_id", "places", ["place_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
