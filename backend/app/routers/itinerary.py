from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

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
    delete_by_id,
    ensure_in_trip,
    get_or_404,
    save_new,
    save_updates,
)

router = APIRouter(tags=["itinerary"])


def _validate_links(db: Session, trip_id: int, place_id: int | None, booking_id: int | None):
    ensure_in_trip(
        db, Place, place_id, trip_id, message="El sitio enlazado no pertenece a este viaje"
    )
    ensure_in_trip(
        db, Booking, booking_id, trip_id, message="La reserva enlazada no pertenece a este viaje"
    )


@router.get("/trips/{trip_id}/itinerary", response_model=list[ItineraryItemRead])
def list_itinerary(trip_id: int, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    return db.scalars(
        select(ItineraryItem)
        .where(ItineraryItem.trip_id == trip_id)
        .order_by(ItineraryItem.day, ItineraryItem.order_index, ItineraryItem.id)
    ).all()


@router.post("/trips/{trip_id}/itinerary", response_model=ItineraryItemRead, status_code=201)
def create_item(trip_id: int, payload: ItineraryItemCreate, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    _validate_links(db, trip_id, payload.place_id, payload.booking_id)
    return save_new(db, ItineraryItem(trip_id=trip_id), payload.model_dump())


@router.patch("/itinerary/{item_id}", response_model=ItineraryItemRead)
def update_item(item_id: int, payload: ItineraryItemUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, ItineraryItem, item_id)
    data = payload.model_dump(exclude_unset=True)
    _validate_links(db, item.trip_id, data.get("place_id"), data.get("booking_id"))
    return save_updates(db, item, data)


@router.delete("/itinerary/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    delete_by_id(db, ItineraryItem, item_id)


@router.get("/trips/{trip_id}/calendar.ics")
def export_calendar(trip_id: int, bookings: bool = True, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    content = build_calendar(db, trip, include_bookings=bookings)
    filename = f"itinerario-{ascii_filename(trip.name, 'viaje')}.ics"
    return Response(
        content=content,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/itinerary/reorder", status_code=204)
def reorder_items(payload: ReorderRequest, db: Session = Depends(get_db)):
    for entry in payload.items:
        item = get_or_404(db, ItineraryItem, entry.id)
        item.day = entry.day
        item.order_index = entry.order_index
    db.commit()
