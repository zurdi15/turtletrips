from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Booking, BookingType, Expense, Trip
from ..schemas.booking import (
    BookingCreate,
    BookingRead,
    BookingUpdate,
    CreateExpenseFromBooking,
)
from ..schemas.expense import ExpenseRead
from .common import apply_updates, get_or_404
from .expenses import TWO_PLACES, resolve_rate

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
def list_bookings(trip_id: int, type: BookingType | None = None, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    query = select(Booking).where(Booking.trip_id == trip_id)
    if type is not None:
        query = query.where(Booking.type == type.value)
    return db.scalars(
        query.order_by(Booking.start_dt.is_(None), Booking.start_dt, Booking.id)
    ).all()


@router.post("/trips/{trip_id}/bookings", response_model=BookingRead, status_code=201)
def create_booking(trip_id: int, payload: BookingCreate, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    booking = Booking(trip_id=trip_id)
    apply_updates(booking, payload.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/bookings/{booking_id}", response_model=BookingRead)
def update_booking(booking_id: int, payload: BookingUpdate, db: Session = Depends(get_db)):
    booking = get_or_404(db, Booking, booking_id)
    apply_updates(booking, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/bookings/{booking_id}", status_code=204)
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = get_or_404(db, Booking, booking_id)
    db.delete(booking)
    db.commit()


@router.post("/bookings/{booking_id}/create-expense", response_model=ExpenseRead, status_code=201)
async def create_expense_from_booking(
    booking_id: int,
    payload: CreateExpenseFromBooking | None = None,
    db: Session = Depends(get_db),
):
    booking = get_or_404(db, Booking, booking_id)
    if booking.cost_amount is None or not booking.cost_currency:
        raise HTTPException(
            status_code=400, detail="La reserva no tiene coste o moneda definidos"
        )
    trip = db.get(Trip, booking.trip_id)
    day = booking.start_dt.date() if booking.start_dt else date.today()
    provided = payload.exchange_rate if payload else None
    currency = booking.cost_currency.upper()
    rate = await resolve_rate(db, trip.base_currency, currency, day, provided)

    amount = Decimal(str(booking.cost_amount))
    expense = Expense(
        trip_id=booking.trip_id,
        booking_id=booking.id,
        day=day,
        category=BOOKING_EXPENSE_CATEGORY.get(booking.type, "Otros"),
        description=booking.title,
        amount=amount,
        currency=currency,
        exchange_rate=rate,
        amount_base=(amount * rate).quantize(TWO_PLACES),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense
