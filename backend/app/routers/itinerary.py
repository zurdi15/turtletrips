import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Booking, ItineraryItem, Place, Trip
from ..schemas.itinerary import (
    ItineraryItemCreate,
    ItineraryItemRead,
    ItineraryItemUpdate,
    ReorderRequest,
)
from ..services.ics import build_calendar
from .common import (
    ascii_filename,
    ensure_in_trip,
    ensure_trip_member,
    get_trip_scoped,
    save_new,
    save_updates,
)

router = APIRouter(tags=["itinerary"])
# feed de suscripción: el token es la llave, queda fuera del candado de sesión
public_router = APIRouter(tags=["itinerary"])


def _validate_links(db: Session, trip_id: int, place_id: int | None, booking_id: int | None):
    ensure_in_trip(
        db, Place, place_id, trip_id, message="El sitio enlazado no pertenece a este viaje"
    )
    ensure_in_trip(
        db, Booking, booking_id, trip_id, message="La reserva enlazada no pertenece a este viaje"
    )


@router.get("/trips/{trip_id}/itinerary", response_model=list[ItineraryItemRead])
def list_itinerary(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    ensure_trip_member(db, user, trip_id)
    return db.scalars(
        select(ItineraryItem)
        .where(ItineraryItem.trip_id == trip_id)
        .order_by(ItineraryItem.day, ItineraryItem.order_index, ItineraryItem.id)
    ).all()


@router.post("/trips/{trip_id}/itinerary", response_model=ItineraryItemRead, status_code=201)
def create_item(
    trip_id: int, payload: ItineraryItemCreate, user: CurrentUser, db: Session = Depends(get_db)
):
    ensure_trip_member(db, user, trip_id)
    _validate_links(db, trip_id, payload.place_id, payload.booking_id)
    return save_new(db, ItineraryItem(trip_id=trip_id), payload.model_dump())


@router.patch("/itinerary/{item_id}", response_model=ItineraryItemRead)
def update_item(
    item_id: int, payload: ItineraryItemUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    item = get_trip_scoped(db, user, ItineraryItem, item_id)
    data = payload.model_dump(exclude_unset=True)
    _validate_links(db, item.trip_id, data.get("place_id"), data.get("booking_id"))
    return save_updates(db, item, data)


@router.delete("/itinerary/{item_id}", status_code=204)
def delete_item(item_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    item = get_trip_scoped(db, user, ItineraryItem, item_id)
    db.delete(item)
    db.commit()


@router.get("/trips/{trip_id}/calendar.ics")
def export_calendar(
    trip_id: int, user: CurrentUser, bookings: bool = True, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
    content = build_calendar(db, trip, include_bookings=bookings)
    filename = f"itinerario-{ascii_filename(trip.name, 'viaje')}.ics"
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/trips/{trip_id}/ics-token")
def rotate_ics_token(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)) -> dict:
    """Genera (o rota, invalidando el anterior) el token de suscripción."""
    trip = ensure_trip_member(db, user, trip_id)
    trip.ics_token = secrets.token_urlsafe(24)
    db.commit()
    return {"token": trip.ics_token}


@public_router.get("/calendar/{token}.ics")
def subscribed_calendar(token: str, bookings: bool = True, db: Session = Depends(get_db)):
    """Feed de suscripción (Google Calendar «Desde URL»): el token es la llave,
    exento tanto de la sesión de la app como de la auth del reverse proxy."""
    trip = db.scalar(select(Trip).where(Trip.ics_token == token)) if token else None
    if trip is None:
        raise HTTPException(status_code=404, detail="Calendario no encontrado")
    content = build_calendar(db, trip, include_bookings=bookings)
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/itinerary/reorder", status_code=204)
def reorder_items(payload: ReorderRequest, user: CurrentUser, db: Session = Depends(get_db)):
    for entry in payload.items:
        item = get_trip_scoped(db, user, ItineraryItem, entry.id)
        item.day = entry.day
        item.order_index = entry.order_index
    db.commit()
