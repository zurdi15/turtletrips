from datetime import date, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import CurrentUser
from ..db import get_db
from ..models import (
    Booking,
    Expense,
    ExpenseShare,
    Place,
    Settlement,
    SplitMode,
    Traveler,
    Trip,
)
from ..schemas.expense import (
    ExpenseCreate,
    ExpenseRead,
    ExpenseShareInput,
    ExpenseUpdate,
    ImportResult,
)
from ..schemas.misc import SettlementCreate, TripBalances
from ..services import csv_io
from ..services.balances import split_amount, trip_balances, validate_shares
from ..services.rates import resolve_rate, to_base
from .common import (
    ascii_filename,
    delete_trip_scoped,
    ensure_in_trip,
    ensure_trip_member,
    get_or_404,
    get_trip_scoped,
    save_new,
    save_updates,
)

router = APIRouter(tags=["expenses"])

PLACE_NOT_IN_TRIP = "El sitio no pertenece a este viaje"


def _enforce_common_exclusivity(data: dict) -> None:
    """paid_by_common y paid_by_id son excluyentes: el último gana.

    Marcar fondo común suelta al pagador; asignar un pagador desmarca el fondo.
    """
    if data.get("paid_by_common"):
        data["paid_by_id"] = None
    elif data.get("paid_by_id") is not None:
        data["paid_by_common"] = False


def _checked_shares(
    trip: Trip, amount: Decimal, split_mode: str, shares: list[ExpenseShareInput]
) -> list[ExpenseShare]:
    """Valida el reparto (400 si es inválido) y construye las filas."""
    try:
        validate_shares(trip, amount, split_mode, shares)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    equal = split_mode == SplitMode.equal.value
    return [
        ExpenseShare(traveler_id=s.traveler_id, value=None if equal else s.value)
        for s in shares
    ]


def _replace_shares(db: Session, expense: Expense, rows: list[ExpenseShare]) -> None:
    """Cambia el reparto entero, vaciando ANTES de meter.

    Si se asigna la lista nueva de golpe, SQLAlchemy puede emitir los INSERT
    antes que los DELETE de las filas viejas y, con (expense_id, traveler_id)
    único, reenviar el MISMO reparto —lo que hace el formulario al guardar
    cualquier campo— moría con IntegrityError.
    """
    if expense.shares:
        expense.shares.clear()
        db.flush()  # aquí salen los DELETE
    expense.shares = rows


@router.get("/trips/{trip_id}/expenses", response_model=list[ExpenseRead])
def list_expenses(
    trip_id: int,
    user: CurrentUser,
    category: str | None = None,
    day: date | None = None,
    paid_by_id: int | None = None,
    db: Session = Depends(get_db),
):
    ensure_trip_member(db, user, trip_id)
    query = select(Expense).where(Expense.trip_id == trip_id)
    if category is not None:
        query = query.where(Expense.category == category)
    if day is not None:
        query = query.where(Expense.day == day)
    if paid_by_id is not None:
        query = query.where(Expense.paid_by_id == paid_by_id)
    return db.scalars(
        query.options(selectinload(Expense.shares))
        .order_by(Expense.day.desc(), Expense.id.desc())
    ).all()


@router.get("/trips/{trip_id}/balances", response_model=TripBalances)
def get_trip_balances(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    return trip_balances(db, trip)


@router.post("/trips/{trip_id}/settlements", response_model=TripBalances, status_code=201)
def create_settlement(
    trip_id: int, payload: SettlementCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    """Registra un pago entre viajeros y devuelve los saldos actualizados."""
    trip = ensure_trip_member(db, user, trip_id)
    if payload.from_id == payload.to_id:
        raise HTTPException(status_code=400, detail="El pagador y el receptor deben ser distintos")
    get_or_404(db, Traveler, payload.from_id)
    get_or_404(db, Traveler, payload.to_id)
    db.add(
        Settlement(
            trip_id=trip_id,
            from_id=payload.from_id,
            to_id=payload.to_id,
            amount_base=payload.amount_base,
        )
    )
    db.commit()
    return trip_balances(db, trip)


@router.delete("/settlements/{settlement_id}", status_code=204)
def delete_settlement(settlement_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    delete_trip_scoped(db, user, Settlement, settlement_id)


@router.post("/trips/{trip_id}/expenses", response_model=ExpenseRead, status_code=201)
async def create_expense(
    trip_id: int, payload: ExpenseCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
    ensure_in_trip(db, Place, payload.place_id, trip_id, message=PLACE_NOT_IN_TRIP)
    currency = (payload.currency or trip.base_currency).upper()
    rate = await resolve_rate(db, trip.base_currency, currency, payload.day, payload.exchange_rate)

    expense = Expense(trip_id=trip_id)
    expense.shares = _checked_shares(
        trip, payload.amount, payload.split_mode.value, payload.shares
    )
    data = payload.model_dump(exclude={"currency", "exchange_rate", "shares"})
    _enforce_common_exclusivity(data)
    data["currency"] = currency
    data["exchange_rate"] = rate
    data["amount_base"] = to_base(payload.amount, rate)
    return save_new(db, expense, data)


@router.patch("/expenses/{expense_id}", response_model=ExpenseRead)
async def update_expense(
    expense_id: int, payload: ExpenseUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    expense = get_trip_scoped(db, user, Expense, expense_id)
    trip = db.get(Trip, expense.trip_id)
    data = payload.model_dump(exclude_unset=True)
    _enforce_common_exclusivity(data)
    if "place_id" in data:
        ensure_in_trip(db, Place, data["place_id"], expense.trip_id, message=PLACE_NOT_IN_TRIP)

    currency_changed = "currency" in data and data["currency"].upper() != expense.currency
    if currency_changed and "exchange_rate" not in data:
        data["exchange_rate"] = await resolve_rate(
            db,
            trip.base_currency,
            data["currency"].upper(),
            data.get("day", expense.day),
            None,
        )
    if "currency" in data:
        data["currency"] = data["currency"].upper()
    amount = Decimal(str(data.get("amount", expense.amount)))
    rate = Decimal(str(data.get("exchange_rate", expense.exchange_rate)))
    data["amount_base"] = to_base(amount, rate)

    new_mode = data["split_mode"].value if "split_mode" in data else expense.split_mode
    if payload.shares is not None:
        # reemplazo completo del reparto ([] + equal = volver al implícito)
        _replace_shares(db, expense, _checked_shares(trip, amount, new_mode, payload.shares))
        data.pop("shares", None)
    elif "amount" in data and new_mode == SplitMode.amount.value and expense.shares:
        # cambia el importe con reparto por importes: rescalar proporcionalmente
        old_values = {s.traveler_id: Decimal(str(s.value or 0)) for s in expense.shares}
        rescaled = split_amount(amount, old_values)
        for share in expense.shares:
            share.value = rescaled.get(share.traveler_id, Decimal(0))
    elif "split_mode" in data:
        # cambio de modo reutilizando los participantes actuales
        current = [
            ExpenseShareInput(traveler_id=s.traveler_id, value=s.value)
            for s in expense.shares
        ]
        _replace_shares(db, expense, _checked_shares(trip, amount, new_mode, current))

    # gasto generado desde una reserva: importe, moneda, pagador y día se
    # espejan de vuelta en la reserva (el título manda desde la reserva)
    if expense.booking_id is not None:
        booking = db.get(Booking, expense.booking_id)
        if booking is not None:
            booking.cost_amount = amount
            booking.cost_currency = data.get("currency", expense.currency)
            booking.paid_by_id = data.get("paid_by_id", expense.paid_by_id)
            booking.paid_by_common = data.get("paid_by_common", expense.paid_by_common)
            # renombrar el gasto renombra la reserva (y viceversa vía sync)
            if "description" in data:
                booking.title = data["description"]
            # mover el día del gasto desplaza entrada/salida conservando la
            # duración de la estancia (y las horas); con tramos, viajan todos
            # (también la vuelta: el conjunto conserva su forma)
            if "day" in data:
                new_day: date = data["day"]
                if booking.start_dt is not None:
                    delta = new_day - booking.start_dt.date()
                    if delta:
                        booking.start_dt += delta
                        if booking.end_dt is not None:
                            booking.end_dt += delta
                        for seg in booking.segments:
                            if seg.departure_dt is not None:
                                seg.departure_dt += delta
                            if seg.arrival_dt is not None:
                                seg.arrival_dt += delta
                elif not booking.segments:
                    # sin fecha ni tramos: estrena start_dt en el día del gasto
                    booking.start_dt = datetime.combine(new_day, time(0, 0))

    return save_updates(db, expense, data)


@router.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    delete_trip_scoped(db, user, Expense, expense_id)


@router.get("/trips/{trip_id}/expenses/export.csv")
def export_expenses(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    content = csv_io.export_csv(db, trip)
    filename = f"gastos-{ascii_filename(trip.name, 'viaje')}.csv"
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/trips/{trip_id}/expenses/import", response_model=ImportResult)
async def import_expenses(
    trip_id: int,
    file: UploadFile,
    user: CurrentUser,
    dry_run: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    trip = ensure_trip_member(db, user, trip_id)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV demasiado grande (máx 5 MB)")
    return csv_io.import_csv(db, trip, content, dry_run=dry_run)
