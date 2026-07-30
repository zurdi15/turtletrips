from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import (
    Booking,
    BookingSegment,
    BookingType,
    Expense,
    ItineraryItem,
    Place,
    PlaceCategory,
    SplitMode,
    Trip,
)
from ..schemas.booking import (
    BookingCreate,
    BookingRead,
    BookingSegmentInput,
    BookingUpdate,
    CreateExpenseFromBooking,
)
from ..schemas.expense import ExpenseRead
from ..services.balances import split_amount
from ..services.booking_place import ensure_booking_place
from ..services.rates import resolve_rate, to_base
from .common import apply_updates, ensure_trip_member, get_trip_scoped

router = APIRouter(tags=["bookings"])

BOOKING_EXPENSE_CATEGORY = {
    BookingType.hotel.value: "Alojamiento",
    BookingType.flight.value: "Vuelos",
    BookingType.train.value: "Transporte",
    BookingType.bus.value: "Transporte",
    BookingType.ferry.value: "Transporte",
    BookingType.car_rental.value: "Transporte",
    BookingType.activity.value: "Tours",
    BookingType.other.value: "Otros",
}


@router.get("/trips/{trip_id}/bookings", response_model=list[BookingRead])
def list_bookings(
    trip_id: int,
    user: CurrentUser,
    type: BookingType | None = None,
    db: Session = Depends(get_db),
):
    ensure_trip_member(db, user, trip_id)
    query = select(Booking).where(Booking.trip_id == trip_id)
    if type is not None:
        query = query.where(Booking.type == type.value)
    return db.scalars(
        query.order_by(Booking.start_dt.is_(None), Booking.start_dt, Booking.id)
    ).all()


def _enforce_common_exclusivity(data: dict) -> None:
    """paid_by_common y paid_by_id son excluyentes: el último gana."""
    if data.get("paid_by_common"):
        data["paid_by_id"] = None
    elif data.get("paid_by_id") is not None:
        data["paid_by_common"] = False


# campos planos que dejan de mandar cuando la reserva tiene tramos
AGGREGATE_FIELDS = {"start_dt", "end_dt", "origin", "destination", "flight_number"}


def _recompute_from_segments(booking: Booking) -> None:
    """Los tramos mandan: los campos planos de ruta/fechas pasan a ser su
    agregado (primera salida, última llegada, extremos de la ruta) y el
    flight_number vive en el tramo."""
    segs = booking.segments
    if not segs:
        return
    departures = [s.departure_dt for s in segs if s.departure_dt is not None]
    arrivals = [s.arrival_dt for s in segs if s.arrival_dt is not None]
    booking.start_dt = min(departures) if departures else None
    booking.end_dt = max(arrivals) if arrivals else None
    booking.origin = segs[0].origin
    booking.destination = segs[-1].destination
    booking.flight_number = None


def _apply_segments(booking: Booking, segments: list[BookingSegmentInput] | None) -> None:
    """REEMPLAZA el conjunto de tramos: ordena por salida (los sin fecha
    conservan el orden del payload, al final), reescribe position y deriva
    los agregados. Con [] solo vacía los tramos (sin tocar campos planos:
    un hotel no debe perder su check-in por mandar la lista vacía)."""
    if segments is None:
        return
    dated = [s for s in segments if s.departure_dt is not None]
    ordered = sorted(dated, key=lambda s: s.departure_dt) + [
        s for s in segments if s.departure_dt is None
    ]
    booking.segments = [
        BookingSegment(
            position=i,
            origin=s.origin,
            destination=s.destination,
            departure_dt=s.departure_dt,
            arrival_dt=s.arrival_dt,
            flight_number=s.flight_number,
        )
        for i, s in enumerate(ordered)
    ]
    _recompute_from_segments(booking)


async def _new_booking_expense(
    db: Session, booking: Booking, provided_rate: Decimal | None
) -> Expense:
    """Construye el gasto espejo de la reserva (no lo añade ni commitea)."""
    trip = db.get(Trip, booking.trip_id)
    day = booking.start_dt.date() if booking.start_dt else date.today()
    currency = booking.cost_currency.upper()
    rate = await resolve_rate(db, trip.base_currency, currency, day, provided_rate)
    amount = Decimal(str(booking.cost_amount))
    return Expense(
        trip_id=booking.trip_id,
        booking_id=booking.id,
        place_id=booking.place_id,
        paid_by_id=booking.paid_by_id,
        paid_by_common=booking.paid_by_common,
        day=day,
        category=BOOKING_EXPENSE_CATEGORY.get(booking.type, "Otros"),
        description=booking.title,
        amount=amount,
        currency=currency,
        exchange_rate=rate,
        amount_base=to_base(amount, rate),
    )


async def _auto_create_expense(db: Session, booking: Booking) -> None:
    """Una reserva con coste tiene siempre su gasto: se crea solo, sin paso
    manual. Best-effort: sin tasa de cambio disponible la reserva se guarda
    igual y el gasto puede generarse a mano después. No commitea."""
    if booking.cost_amount is None or not booking.cost_currency:
        return
    if db.scalar(select(Expense.id).where(Expense.booking_id == booking.id)) is not None:
        return
    try:
        db.add(await _new_booking_expense(db, booking, None))
    except HTTPException:
        pass


async def _sync_linked_expense(db: Session, booking: Booking) -> None:
    """La reserva es el registro maestro de su gasto generado: al editarla,
    el gasto se mantiene espejo (título, fecha, sitio, pagador e importe).
    No commitea."""
    expense = db.scalar(select(Expense).where(Expense.booking_id == booking.id))
    if expense is None:
        return
    expense.description = booking.title
    if booking.start_dt is not None:
        expense.day = booking.start_dt.date()
    expense.place_id = booking.place_id
    expense.paid_by_id = booking.paid_by_id
    expense.paid_by_common = booking.paid_by_common
    if booking.cost_amount is None or not booking.cost_currency:
        return
    amount = Decimal(str(booking.cost_amount))
    currency = booking.cost_currency.upper()
    if currency != expense.currency:
        trip = db.get(Trip, booking.trip_id)
        rate = await resolve_rate(db, trip.base_currency, currency, expense.day, None)
        expense.currency = currency
        expense.exchange_rate = rate
    if amount != Decimal(str(expense.amount)):
        # reparto por importes: rescalar proporcionalmente (como PATCH /expenses)
        if expense.split_mode == SplitMode.amount.value and expense.shares:
            old = {s.traveler_id: Decimal(str(s.value or 0)) for s in expense.shares}
            rescaled = split_amount(amount, old)
            for share in expense.shares:
                share.value = rescaled.get(share.traveler_id, Decimal(0))
        expense.amount = amount
    expense.amount_base = to_base(amount, Decimal(str(expense.exchange_rate)))


@router.post("/trips/{trip_id}/bookings", response_model=BookingRead, status_code=201)
async def create_booking(
    trip_id: int, payload: BookingCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_trip_member(db, user, trip_id)
    booking = Booking(trip_id=trip_id)
    data = payload.model_dump()
    data.pop("segments", None)  # los tramos no van por apply_updates
    _enforce_common_exclusivity(data)
    apply_updates(booking, data)
    _apply_segments(booking, payload.segments)
    db.add(booking)
    ensure_booking_place(db, booking)
    db.flush()  # id de la reserva para el gasto enlazado
    await _auto_create_expense(db, booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/bookings/{booking_id}", response_model=BookingRead)
async def update_booking(
    booking_id: int, payload: BookingUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    booking = get_trip_scoped(db, user, Booking, booking_id)
    data = payload.model_dump(exclude_unset=True)
    has_segments = data.pop("segments", None) is not None
    _enforce_common_exclusivity(data)
    apply_updates(booking, data)
    if has_segments:
        _apply_segments(booking, payload.segments)
    elif booking.segments and AGGREGATE_FIELDS & data.keys():
        # tocar los campos planos de una reserva con tramos no los desincroniza
        _recompute_from_segments(booking)
    # coordenadas nuevas → el sitio enlazado deja de valer y se recalcula
    if "lat" in data or "lon" in data:
        booking.place_id = None
    ensure_booking_place(db, booking)
    await _sync_linked_expense(db, booking)
    # si la reserva estrena coste y aún no tiene gasto, se crea ahora
    await _auto_create_expense(db, booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    booking = get_trip_scoped(db, user, Booking, booking_id)
    # el gasto espejo muere con la reserva
    expense = db.scalar(select(Expense).where(Expense.booking_id == booking.id))
    if expense is not None:
        db.delete(expense)
    place = db.get(Place, booking.place_id) if booking.place_id is not None else None
    db.delete(booking)
    db.flush()
    # el sitio de alojamiento autocreado se limpia si queda huérfano; ciudades
    # y POIs enlazados por cercanía no se tocan
    if place is not None and place.category == PlaceCategory.lodging.value:
        in_use = (
            db.scalar(select(Booking.id).where(Booking.place_id == place.id)) is not None
            or db.scalar(select(Expense.id).where(Expense.place_id == place.id)) is not None
            or db.scalar(
                select(ItineraryItem.id).where(ItineraryItem.place_id == place.id)
            )
            is not None
        )
        if not in_use:
            db.delete(place)
    db.commit()


@router.post("/bookings/{booking_id}/create-expense", response_model=ExpenseRead, status_code=201)
async def create_expense_from_booking(
    booking_id: int,
    user: CurrentUser,
    payload: CreateExpenseFromBooking | None = None,
    db: Session = Depends(get_db),
):
    booking = get_trip_scoped(db, user, Booking, booking_id)
    if booking.cost_amount is None or not booking.cost_currency:
        raise HTTPException(
            status_code=400, detail="La reserva no tiene coste o moneda definidos"
        )
    # una reserva genera como mucho un gasto; borrar el gasto (no la reserva)
    # permite volver a generarlo
    if db.scalar(select(Expense.id).where(Expense.booking_id == booking.id)) is not None:
        raise HTTPException(status_code=400, detail="La reserva ya tiene un gasto enlazado")
    provided = payload.exchange_rate if payload else None
    expense = await _new_booking_expense(db, booking, provided)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense
