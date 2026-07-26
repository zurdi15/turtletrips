"""plantillas de maleta por viajero (antes por familia)

Revision ID: b3e1c7a90d24
Revises: caf68993213e
Create Date: 2026-07-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b3e1c7a90d24"
down_revision: Union[str, None] = "caf68993213e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NAMING = {"uq": "uq_%(table_name)s_%(column_0_name)s"}


def upgrade() -> None:
    with op.batch_alter_table("packing_templates", naming_convention=NAMING) as batch_op:
        batch_op.add_column(sa.Column("traveler_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_packing_templates_traveler_id_travelers",
            "travelers",
            ["traveler_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # --- backfill ---
    # 1) plantilla que se llama como un viajero de la familia → es SU maleta
    # 2) el resto, al primer admin de la familia (fallbacks: usuario más
    #    antiguo de la familia; después, viajero más antiguo)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE packing_templates SET traveler_id = (
                SELECT t.id FROM travelers t
                WHERE t.family_id = packing_templates.family_id
                  AND LOWER(t.name) = LOWER(packing_templates.name)
                ORDER BY t.id LIMIT 1
            ) WHERE traveler_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE packing_templates SET traveler_id = (
                SELECT u.traveler_id FROM users u
                JOIN travelers t ON t.id = u.traveler_id
                WHERE t.family_id = packing_templates.family_id AND u.is_admin = 1
                ORDER BY u.id LIMIT 1
            ) WHERE traveler_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE packing_templates SET traveler_id = (
                SELECT u.traveler_id FROM users u
                JOIN travelers t ON t.id = u.traveler_id
                WHERE t.family_id = packing_templates.family_id
                ORDER BY u.id LIMIT 1
            ) WHERE traveler_id IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE packing_templates SET traveler_id = (
                SELECT t.id FROM travelers t
                WHERE t.family_id = packing_templates.family_id
                ORDER BY t.id LIMIT 1
            ) WHERE traveler_id IS NULL
            """
        )
    )
    # familia sin ningún viajero: la plantilla no puede tener dueño (caso imposible
    # en la práctica, pero el NOT NULL de abajo no puede fallar)
    conn.execute(sa.text("DELETE FROM packing_templates WHERE traveler_id IS NULL"))

    # duplicados de nombre dentro del mismo dueño (dos familias fusionadas en un
    # mismo viajero no pueden violar el unique nuevo): sufijo con el id
    conn.execute(
        sa.text(
            """
            UPDATE packing_templates SET name = name || ' (' || id || ')'
            WHERE id NOT IN (
                SELECT MIN(id) FROM packing_templates GROUP BY traveler_id, LOWER(name)
            )
            """
        )
    )

    # --- NOT NULL + swap del unique por familia → por viajero, fuera family_id ---
    with op.batch_alter_table("packing_templates", naming_convention=NAMING) as batch_op:
        batch_op.alter_column("traveler_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_constraint("uq_packing_templates_family_name", type_="unique")
        batch_op.create_unique_constraint(
            "uq_packing_templates_traveler_name", ["traveler_id", "name"]
        )
        batch_op.drop_constraint(
            "fk_packing_templates_family_id_families", type_="foreignkey"
        )
        batch_op.drop_column("family_id")


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
