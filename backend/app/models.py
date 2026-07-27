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
    Index,
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
    lodging = "lodging"
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


class SplitMode(str, enum.Enum):
    equal = "equal"  # partes iguales (sin filas = implícito entre todos los viajeros)
    amount = "amount"  # importes personalizados en la moneda del gasto
    percent = "percent"  # porcentajes personalizados (0-100)


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
    # la lista de viajes filtra por viajero en cada carga de la home
    Index("ix_trip_travelers_traveler_id", "traveler_id"),
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
    album_url: Mapped[str | None] = mapped_column(String(500))  # enlace a álbum de fotos externo
    # llave secreta del feed .ics de suscripción (URL pública sin auth)
    ics_token: Mapped[str | None] = mapped_column(String(64), unique=True)
    notes: Mapped[str | None] = mapped_column(Text)
    # familia del creador: determina qué categorías/plantillas usa el viaje.
    # Nullable como red de seguridad para datos legacy; la app siempre lo asigna.
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="SET NULL")
    )

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
    settlements: Mapped[list["Settlement"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    day_journals: Mapped[list["DayJournal"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="trip", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def debts_settled(self) -> bool:
        """True si hubo liquidaciones registradas y los saldos quedan a cero."""
        from .services.balances import trip_debts_settled  # import tardío: evita ciclo

        return trip_debts_settled(self)

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


class Family(TimestampMixin, Base):
    """Grupo de viajeros (con o sin cuenta): scoping de mapa, categorías y plantillas."""

    __tablename__ = "families"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # orden manual (drag & drop en /travelers)
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Traveler(TimestampMixin, Base):
    """Viajero global, reutilizable entre viajes.

    Puede tener cuenta de usuario asociada (User.traveler_id) o ser "virtual"
    (niños, invitados sin cuenta). Pertenece como mucho a una familia.
    """

    __tablename__ = "travelers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    color: Mapped[str | None] = mapped_column(String(7))
    family_id: Mapped[int | None] = mapped_column(
        ForeignKey("families.id", ondelete="RESTRICT")
    )
    # nombre del fichero guardado en uploads/avatars (como Trip.cover_image)
    avatar_image: Mapped[str | None] = mapped_column(String(100))

    family: Mapped["Family | None"] = relationship()
    user: Mapped["User | None"] = relationship(
        back_populates="traveler", lazy="selectin"
    )

    @property
    def avatar_url(self) -> str | None:
        if not self.avatar_image:
            return None
        return f"/api/v1/travelers/{self.id}/avatar?v={self.avatar_image}"

    @property
    def has_user(self) -> bool:
        return self.user is not None


class User(TimestampMixin, Base):
    """Cuenta de acceso. Siempre vinculada 1:1 a un viajero (su identidad)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)  # lookup case-insensitive
    password_hash: Mapped[str] = mapped_column(String(100))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    traveler_id: Mapped[int] = mapped_column(
        ForeignKey("travelers.id", ondelete="RESTRICT"), unique=True
    )
    # preferencias de UI por usuario (viven en DB, no en localStorage)
    theme: Mapped[str] = mapped_column(String(10), default="light")  # light|dark|system
    language: Mapped[str] = mapped_column(String(5), default="en")  # es|en

    traveler: Mapped[Traveler] = relationship(back_populates="user")


class UserSession(Base):
    """Sesión server-side: el token viaja en cookie y se guarda hasheado (sha256).

    Tokens aleatorios de entropía plena → sin claves de firma que gestionar.
    """

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    user: Mapped[User] = relationship()


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
    # número de vuelo (IB6801); solo aplica a reservas de tipo flight
    flight_number: Mapped[str | None] = mapped_column(String(20))
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
    # sitio enlazado automáticamente a partir de las coordenadas de la reserva
    place_id: Mapped[int | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL")
    )
    # pagador del coste: lo hereda el gasto generado (mismo modelo que Expense)
    paid_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("travelers.id", ondelete="SET NULL")
    )
    paid_by_common: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )

    trip: Mapped[Trip] = relationship(back_populates="bookings")
    place: Mapped["Place | None"] = relationship()
    paid_by: Mapped["Traveler | None"] = relationship()
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
    # pagado del fondo/monedero común (excluyente con paid_by_id): cuenta en
    # los totales pero no en los saldos entre viajeros
    paid_by_common: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0"
    )
    split_mode: Mapped[str] = mapped_column(
        String(10), default=SplitMode.equal.value, server_default=SplitMode.equal.value
    )
    notes: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[Trip] = relationship(back_populates="expenses")
    paid_by: Mapped[Traveler | None] = relationship()
    shares: Mapped[list["ExpenseShare"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ExpenseShare.traveler_id",
    )


class ExpenseShare(Base):
    """Participación de un viajero en un gasto.

    value según split_mode del gasto: NULL en equal (solo marca participación),
    importe en la moneda del gasto en amount, 0-100 en percent.
    """

    __tablename__ = "expense_shares"
    __table_args__ = (UniqueConstraint("expense_id", "traveler_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), index=True
    )
    traveler_id: Mapped[int] = mapped_column(
        ForeignKey("travelers.id", ondelete="CASCADE")
    )
    value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    expense: Mapped[Expense] = relationship(back_populates="shares")


class Settlement(TimestampMixin, Base):
    """Pago registrado entre viajeros para saldar deudas (en moneda base)."""

    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    from_id: Mapped[int] = mapped_column(ForeignKey("travelers.id", ondelete="CASCADE"))
    to_id: Mapped[int] = mapped_column(ForeignKey("travelers.id", ondelete="CASCADE"))
    amount_base: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    trip: Mapped[Trip] = relationship(back_populates="settlements")
    from_traveler: Mapped[Traveler] = relationship(foreign_keys=[from_id])
    to_traveler: Mapped[Traveler] = relationship(foreign_keys=[to_id])


class Attachment(TimestampMixin, Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    booking_id: Mapped[int | None] = mapped_column(
        ForeignKey("bookings.id", ondelete="SET NULL")
    )
    # recibo de un gasto; al borrar el gasto queda como fichero del viaje
    expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("expenses.id", ondelete="SET NULL")
    )
    original_name: Mapped[str] = mapped_column(String(300))
    stored_name: Mapped[str] = mapped_column(String(100))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)

    trip: Mapped[Trip] = relationship(back_populates="attachments")
    booking: Mapped["Booking | None"] = relationship(back_populates="attachments")


class DayJournal(TimestampMixin, Base):
    """Diario (texto libre) y postal (una foto) por día de un viaje.

    Único por (trip_id, day). No hay entidad "día": los días de la agenda se
    derivan de las fechas, así que el diario se ancla directamente a la fecha.
    """

    __tablename__ = "day_journals"
    __table_args__ = (UniqueConstraint("trip_id", "day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date, index=True)
    text: Mapped[str | None] = mapped_column(Text)
    # nombre del fichero guardado (como Trip.cover_image); la ruta la resuelve services/files
    photo_image: Mapped[str | None] = mapped_column(String(100))

    trip: Mapped[Trip] = relationship(back_populates="day_journals")

    @property
    def photo_url(self) -> str | None:
        if not self.photo_image:
            return None
        return (
            f"/api/v1/trips/{self.trip_id}/journal/"
            f"{self.day.isoformat()}/photo?v={self.photo_image}"
        )


class ChecklistItem(TimestampMixin, Base):
    """Tarea pre-viaje (visados, seguro, check-in…), aparte de la maleta."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    due_date: Mapped[date | None] = mapped_column(Date)
    url: Mapped[str | None] = mapped_column(String(500))  # enlace (web del visado, seguro…)
    notes: Mapped[str | None] = mapped_column(Text)

    trip: Mapped[Trip] = relationship(back_populates="checklist_items")


class Category(TimestampMixin, Base):
    """Categorías configurables para gastos y maleta, propias de cada familia."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint(
            "family_id", "kind", "name", name="uq_categories_family_kind_name"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE")
    )
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
    """Maleta guardada como plantilla reutilizable entre viajes (por viajero).

    El dueño puede ser un viajero con cuenta (sus plantillas) o un virtual
    (la maleta recurrente de un niño, gestionada por los usuarios de su familia).
    """

    __tablename__ = "packing_templates"
    __table_args__ = (
        UniqueConstraint("traveler_id", "name", name="uq_packing_templates_traveler_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    traveler_id: Mapped[int] = mapped_column(
        ForeignKey("travelers.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(100))

    traveler: Mapped[Traveler] = relationship()

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
    """Diario mundial de una familia: lugares visitados, a mano o derivados de viajes."""

    __tablename__ = "world_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    family_id: Mapped[int] = mapped_column(
        ForeignKey("families.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str] = mapped_column(String(10), default="place")  # country|city|place
    country_code: Mapped[str | None] = mapped_column(String(2))  # ISO alpha-2
    lat: Mapped[float | None] = mapped_column()
    lon: Mapped[float | None] = mapped_column()
    note: Mapped[str | None] = mapped_column(Text)
    # cuándo se visitó (retroactivo o heredado del viaje): alimenta las stats anuales
    visited_year: Mapped[int | None] = mapped_column(Integer)
    visited_month: Mapped[int | None] = mapped_column(Integer)  # 1-12
    # postal (una foto), como la del diario de viaje; ficheros en uploads/world/
    photo_image: Mapped[str | None] = mapped_column(String(100))
    auto: Mapped[bool] = mapped_column(Boolean, default=False)  # derivado de un viaje
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)  # auto "borrado" por el usuario
    origin: Mapped[str | None] = mapped_column(String(200))  # nombre del viaje de origen
    trip_place_id: Mapped[int | None] = mapped_column(
        ForeignKey("places.id", ondelete="SET NULL")
    )

    @property
    def photo_url(self) -> str | None:
        if not self.photo_image:
            return None
        return f"/api/v1/world-places/{self.id}/photo?v={self.photo_image}"


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
