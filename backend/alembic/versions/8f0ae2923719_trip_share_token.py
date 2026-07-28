"""trip share token

Revision ID: 8f0ae2923719
Revises: 70cdf16f12c9
Create Date: 2026-07-28 17:24:07.913632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8f0ae2923719'
down_revision: Union[str, None] = '70cdf16f12c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.add_column(sa.Column('share_token', sa.String(length=64), nullable=True))
        # server_default para las filas que ya existen: sin él, NOT NULL falla
        batch_op.add_column(
            sa.Column('share_scopes', sa.JSON(), server_default='[]', nullable=False)
        )
        batch_op.create_unique_constraint('uq_trips_share_token', ['share_token'])


def downgrade() -> None:
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.drop_constraint('uq_trips_share_token', type_='unique')
        batch_op.drop_column('share_scopes')
        batch_op.drop_column('share_token')
