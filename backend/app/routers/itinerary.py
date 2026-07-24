from fastapi import APIRouter, Depends, HTTPException
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
from .common import apply_updates, get_or_404

router = APIRouter(tags=["itinerary"])


def _validate_links(db: Session, trip_id: int, place_id: int | None, booking_id: int | None):
    if place_id is not None:
        place = db.get(Place, place_id)
        if place is None or place.trip_id != trip_id:
            raise HTTPException(status_code=400, detail="El sitio enlazado no pertenece a este viaje")
    if booking_id is not None:
        booking = db.get(Booking, booking_id)
        if booking is None or booking.trip_id != trip_id:
            raise HTTPException(status_code=400, detail="La reserva enlazada no pertenece a este viaje")


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
    item = ItineraryItem(trip_id=trip_id)
    apply_updates(item, payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/itinerary/{item_id}", response_model=ItineraryItemRead)
def update_item(item_id: int, payload: ItineraryItemUpdate, db: Session = Depends(get_db)):
    item = get_or_404(db, ItineraryItem, item_id)
    data = payload.model_dump(exclude_unset=True)
    _validate_links(
        db, item.trip_id, data.get("place_id"), data.get("booking_id")
    )
    apply_updates(item, data)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/itinerary/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = get_or_404(db, ItineraryItem, item_id)
    db.delete(item)
    db.commit()


@router.post("/itinerary/reorder", status_code=204)
def reorder_items(payload: ReorderRequest, db: Session = Depends(get_db)):
    for entry in payload.items:
        item = get_or_404(db, ItineraryItem, entry.id)
        item.day = entry.day
        item.order_index = entry.order_index
    db.commit()
