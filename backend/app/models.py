import enum
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class TripStatus(str, enum.Enum):
    planning = "planning"
    upcoming = "upcoming"
    ongoing = "ongoing"
    done = "done"


class PlaceCategory(str, enum.Enum):
    sight = "sight"
    food = "food"
    museum = "museum"
    nature = "nature"
    viewpoint = "viewpoint"
    shopping = "shopping"
    city = "city"
    town = "town"
    other = "other"


class BookingType(str, enum.Enum):
    hotel = "hotel"
    flight = "flight"
    train = "train"
    bus = "bus"
    ferry = "ferry"
    car_rental = "car_rental"
    activity = "activity"
    other = "other"


class CategoryKind(str, enum.Enum):
    expense = "expense"
    packing = "packing"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


trip_travelers = Table(
    "trip_travelers",
    Base.metadata,
    Column("trip_id", ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True),
    Column("traveler_id", ForeignKey("travelers.id", ondelete="CASCADE"), primary_key=True),
)


class Trip(TimestampMixin, Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    countries: Mapped[list] = mapped_column(JSON, default=list)  # códigos ISO alpha-2
    cover_image: Mapped[str | None] = mapped_column(String(100))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    # NULL = estado auto-derivado de las fechas; un valor = override manual
    status_override: Mapped[str | None] = mapped_column(String(20))
    base_currency: Mapped[str] = mapped_column(String(3), default="EUR")
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    travelers: Mapped[list["Traveler"]] = relationship(
        secondary=trip_travelers, order_by="Traveler.name", passive_deletes=True
    )
    places: Mapped[list["Place"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    itinerary_items: Mapped[list["ItineraryItem"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    expenses: Mapped[list["Expense"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    packing_items: Mapped[list["PackingItem"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    packing_selections: Mapped[list["PackingSelection"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def status(self) -> str:
        """Estado efectivo: override manual si existe, si no derivado de fechas."""
        if self.status_override:
            return self.status_override
        if not self.start_date:
            return TripStatus.planning.value
        today = date.today()
        if today < self.start_date:
            return TripStatus.upcoming.value
        end = self.end_date or self.start_date
        return TripStatus.ongoing.value if today <= end else TripStatus.done.value

    @property
    def cover_url(self) -> str | None:
        if not self.cover_image:
            return None
        return f"/api/v1/trips/{self.id}/cover?v={self.cover_image}"


class Traveler(TimestampMixin, Base):
    """Viajero global, reutilizable entre viajes. No es una cuenta de usuario."""

    __tablename__ = "travelers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str | None] = mapped_column(String(7))


class Place(TimestampMixin, Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(20), default=PlaceCategory.other.value)
    notes: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(String(500))
    lat: Mapped[float | None] = mapped_column()
    lon: Mapped[float | None] = mapped_column()
    visited: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)

    trip: Mapped[Trip] = relationship(back_populates="places")


class ItineraryItem(TimestampMixin, Base):
    __tablename__ = "itinerary_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date, index=True)
    end_day: Mapped[date | None] = mapped_column(Date)  # para estancias de varios días
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    place_id: Mapped[int | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL")
    )
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL")
    )

    trip: Mapped[Trip] = relationship(back_populates="itinerary_items")
    place: Mapped["Place | None"] = relationship()
    booking: Mapped["Booking | None"] = relationship()


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(20), default=BookingType.other.value)
    title: Mapped[str] = mapped_column(String(300))
    provider: Mapped[str | None] = mapped_column(String(200))
    confirmation_code: Mapped[str | None] = mapped_column(String(100))
    start_dt: Mapped[datetime | None] = mapped_column(DateTime)
    end_dt: Mapped[datetime | None] = mapped_column(DateTime)
    origin: Mapped[str | None] = mapped_column(String(200))
    destination: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(500))
    lat: Mapped[float | None] = mapped_column()
    lon: Mapped[float | None] = mapped_column()
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cost_currency: Mapped[str | None] = mapped_column(String(3))
    notes: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[Trip] = relationship(back_populates="bookings")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="booking")


class Expense(TimestampMixin, Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL")
    )
    place_id: Mapped[int | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL")
    )
    day: Mapped[date] = mapped_column(Date, index=True)
    category: Mapped[str] = mapped_column(String(50), default="Otros")
    description: Mapped[str] = mapped_column(String(300))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(16, 6), default=Decimal(1))
    amount_base: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    paid_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("travelers.id", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[Trip] = relationship(back_populates="expenses")
    paid_by: Mapped[Traveler | None] = relationship()


class Attachment(TimestampMixin, Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL")
    )
    original_name: Mapped[str] = mapped_column(String(300))
    stored_name: Mapped[str] = mapped_column(String(100))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)

    trip: Mapped[Trip] = relationship(back_populates="attachments")
    booking: Mapped["Booking | None"] = relationship(back_populates="attachments")


class Category(TimestampMixin, Base):
    """Categorías configurables para gastos y maleta."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("kind", "name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))  # expense | packing
    name: Mapped[str] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(7))
    position: Mapped[int] = mapped_column(Integer, default=0)


class PackingItem(TimestampMixin, Base):
    __tablename__ = "packing_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    # NULL = maleta común del viaje; si no, la maleta de ese viajero
    traveler_id: Mapped[int | None] = mapped_column(
        ForeignKey("travelers.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), default="Ropa")
    url: Mapped[str | None] = mapped_column(String(500))  # enlace de compra
    checked: Mapped[bool] = mapped_column(Boolean, default=False)

    trip: Mapped[Trip] = relationship(back_populates="packing_items")


class PackingSelection(Base):
    """Plantilla seleccionada para la maleta de un viajero (o la común) en un viaje."""

    __tablename__ = "packing_selections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    traveler_id: Mapped[int | None] = mapped_column(
        ForeignKey("travelers.id", ondelete="CASCADE")
    )
    template_id: Mapped[int] = mapped_column(
        ForeignKey("packing_templates.id", ondelete="CASCADE")
    )


class PackingTemplate(TimestampMixin, Base):
    """Maleta guardada como plantilla reutilizable entre viajes."""

    __tablename__ = "packing_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    items: Mapped[list["PackingTemplateItem"]] = relationship(
        back_populates="template", cascade="all, delete-orphan", passive_deletes=True
    )


class PackingTemplateItem(Base):
    __tablename__ = "packing_template_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("packing_templates.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50), default="Ropa")
    url: Mapped[str | None] = mapped_column(String(500))

    template: Mapped[PackingTemplate] = relationship(back_populates="items")


class WorldPlace(TimestampMixin, Base):
    """Diario mundial: lugares visitados, añadidos a mano o derivados de los viajes."""

    __tablename__ = "world_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="place")  # country|city|place
    country_code: Mapped[str | None] = mapped_column(String(2))  # ISO alpha-2
    lat: Mapped[float | None] = mapped_column()
    lon: Mapped[float | None] = mapped_column()
    note: Mapped[str | None] = mapped_column(Text)
    auto: Mapped[bool] = mapped_column(Boolean, default=False)  # derivado de un viaje
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)  # auto "borrado" por el usuario
    origin: Mapped[str | None] = mapped_column(String(200))  # nombre del viaje de origen
    trip_place_id: Mapped[int | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL")
    )


class ExchangeRateCache(Base):
    __tablename__ = "exchange_rate_cache"
    __table_args__ = (UniqueConstraint("base", "quote", "day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base: Mapped[str] = mapped_column(String(3))
    quote: Mapped[str] = mapped_column(String(3))
    day: Mapped[date] = mapped_column(Date)
    rate: Mapped[Decimal] = mapped_column(Numeric(16, 6))


DEFAULT_EXPENSE_CATEGORIES = [
    ("Comida", "#f59e0b"),
    ("Transporte", "#0ea5e9"),
    ("Alojamiento", "#8b5cf6"),
    ("Tours", "#16a34a"),
    ("Entradas", "#e11d48"),
    ("Souvenirs", "#ec4899"),
    ("Gasolina", "#f97316"),
    ("Vuelos", "#6366f1"),
    ("Otros", "#94a3b8"),
]

DEFAULT_PACKING_CATEGORIES = [
    ("Botiquín", "#e11d48"),
    ("Ropa", "#0ea5e9"),
    ("Tecnología", "#8b5cf6"),
]
