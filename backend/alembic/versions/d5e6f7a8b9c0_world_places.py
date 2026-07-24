"""diario mundial: tabla world_places

Revision ID: d5e6f7a8b9c0
Revises: c9d0e1f2a3b4
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "world_places",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
