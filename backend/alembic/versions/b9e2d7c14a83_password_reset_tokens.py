"""enlaces de recuperación de contraseña

Revision ID: b9e2d7c14a83
Revises: c1bf988e03a5
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b9e2d7c14a83"
down_revision: Union[str, None] = "c1bf988e03a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # misma forma que `sessions`: en DB solo el sha256 del token
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user_id", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")
