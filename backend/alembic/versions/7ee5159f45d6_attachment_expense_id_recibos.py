"""attachment expense_id (recibos)

Revision ID: 7ee5159f45d6
Revises: a5cd4a17e429
Create Date: 2026-07-27 17:16:56.175373

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7ee5159f45d6'
down_revision: Union[str, None] = 'a5cd4a17e429'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('expense_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_attachments_expense_id', 'expenses', ['expense_id'], ['id'], ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('attachments', schema=None) as batch_op:
        batch_op.drop_constraint('fk_attachments_expense_id', type_='foreignkey')
        batch_op.drop_column('expense_id')
