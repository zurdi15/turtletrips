"""countries, cover, packing, categorías configurables y viajeros globales

Revision ID: a1b2c3d4e5f6
Revises: f50a5aa20f4c
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f50a5aa20f4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# mapeo de las antiguas categorías (enum en inglés) a las nuevas configurables
OLD_CATEGORY_MAP = {
    "food": "Comida",
    "transport": "Transporte",
    "lodging": "Alojamiento",
    "activities": "Tours",
    "shopping": "Souvenirs",
    "fees": "Otros",
    "other": "Otros",
}


def upgrade() -> None:
    conn = op.get_bind()

    # --- trips: países (multi), portada; fuera destination ---
    with op.batch_alter_table("trips") as batch:
        batch.add_column(sa.Column("countries", sa.JSON(), nullable=False, server_default="[]"))
        batch.add_column(sa.Column("cover_image", sa.String(100), nullable=True))
        batch.drop_column("destination")

    # --- itinerario: rango de fechas ---
    op.add_column("itinerary_items", sa.Column("end_day", sa.Date(), nullable=True))

    # --- categorías configurables ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.UniqueConstraint("kind", "name"),
    )

    # --- maleta ---
    op.create_table(
        "packing_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("checked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_packing_items_trip_id", "packing_items", ["trip_id"])
    op.create_table(
        "packing_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_table(
        "packing_template_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("packing_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("url", sa.String(500), nullable=True),
    )
    op.create_index("ix_packing_template_items_template_id", "packing_template_items", ["template_id"])

    # --- viajeros globales (antes trip_members por viaje) ---
    op.create_table(
        "travelers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_table(
        "trip_travelers",
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("traveler_id", sa.Integer(), sa.ForeignKey("travelers.id", ondelete="CASCADE"), primary_key=True),
    )

    # migrar datos: un viajero global por nombre (case-insensitive)
    members = conn.execute(
        sa.text("SELECT id, trip_id, name, color FROM trip_members ORDER BY id")
    ).fetchall()
    traveler_by_name: dict[str, int] = {}
    member_to_traveler: dict[int, int] = {}
    for member in members:
        key = member.name.strip().lower()
        if key not in traveler_by_name:
            result = conn.execute(
                sa.text("INSERT INTO travelers (name, color) VALUES (:name, :color)"),
                {"name": member.name.strip(), "color": member.color},
            )
            traveler_by_name[key] = result.lastrowid
        member_to_traveler[member.id] = traveler_by_name[key]
        conn.execute(
            sa.text(
                "INSERT OR IGNORE INTO trip_travelers (trip_id, traveler_id) VALUES (:t, :v)"
            ),
            {"t": member.trip_id, "v": traveler_by_name[key]},
        )

    # remapear expenses.paid_by_id (en dos pasos para evitar colisiones de ids)
    for member_id, traveler_id in member_to_traveler.items():
        conn.execute(
            sa.text("UPDATE expenses SET paid_by_id = :neg WHERE paid_by_id = :old"),
            {"neg": -traveler_id, "old": member_id},
        )
    conn.execute(sa.text("UPDATE expenses SET paid_by_id = -paid_by_id WHERE paid_by_id < 0"))

    # reconstruir expenses con la FK apuntando a travelers
    op.rename_table("expenses", "expenses_old")
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.String(300), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(16, 6), nullable=False),
        sa.Column("amount_base", sa.Numeric(14, 2), nullable=False),
        sa.Column("paid_by_id", sa.Integer(), sa.ForeignKey("travelers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    conn.execute(
        sa.text(
            "INSERT INTO expenses (id, trip_id, booking_id, day, category, description, amount, "
            "currency, exchange_rate, amount_base, paid_by_id, notes, created_at, updated_at) "
            "SELECT id, trip_id, booking_id, day, category, description, amount, currency, "
            "exchange_rate, amount_base, paid_by_id, notes, created_at, updated_at FROM expenses_old"
        )
    )
    op.drop_table("expenses_old")
    op.create_index("ix_expenses_trip_id", "expenses", ["trip_id"])
    op.create_index("ix_expenses_day", "expenses", ["day"])

    op.drop_table("trip_members")

    # las categorías antiguas (enum en inglés) pasan a los nuevos nombres
    for old, new in OLD_CATEGORY_MAP.items():
        conn.execute(
            sa.text("UPDATE expenses SET category = :new WHERE category = :old"),
            {"new": new, "old": old},
        )


def downgrade() -> None:
    raise NotImplementedError("downgrade no soportado")
