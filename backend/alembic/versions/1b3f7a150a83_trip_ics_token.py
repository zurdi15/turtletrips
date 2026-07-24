"""trip ics token

Revision ID: 1b3f7a150a83
Revises: d09f8ce4248a
Create Date: 2026-07-24 15:17:48.785643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1b3f7a150a83'
down_revision: Union[str, None] = 'd09f8ce4248a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ics_token', sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint('uq_trips_ics_token', ['ics_token'])


def downgrade() -> None:
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.drop_constraint('uq_trips_ics_token', type_='unique')
        batch_op.drop_column('ics_token')
