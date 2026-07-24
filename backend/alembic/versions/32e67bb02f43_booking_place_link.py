"""booking place link

Revision ID: 32e67bb02f43
Revises: 56e772e57c8f
Create Date: 2026-07-24 13:41:26.088351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '32e67bb02f43'
down_revision: Union[str, None] = '56e772e57c8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('place_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_bookings_place_id', 'places', ['place_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bookings_place_id', type_='foreignkey')
        batch_op.drop_column('place_id')
