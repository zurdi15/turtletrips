"""booking payer

Revision ID: d09f8ce4248a
Revises: 32e67bb02f43
Create Date: 2026-07-24 14:04:57.842955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd09f8ce4248a'
down_revision: Union[str, None] = '32e67bb02f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('paid_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('paid_by_common', sa.Boolean(), server_default='0', nullable=False)
        )
        batch_op.create_foreign_key(
            'fk_bookings_paid_by_id', 'travelers', ['paid_by_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bookings_paid_by_id', type_='foreignkey')
        batch_op.drop_column('paid_by_common')
        batch_op.drop_column('paid_by_id')
