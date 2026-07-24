from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Place, PlaceCategory, Trip
from ..schemas.place import PlaceCreate, PlaceRead, PlaceUpdate
from .common import apply_updates, get_or_404

router = APIRouter(tags=["places"])


@router.get("/trips/{trip_id}/places", response_model=list[PlaceRead])
def list_places(
    trip_id: int,
    visited: bool | None = None,
    category: PlaceCategory | None = None,
    db: Session = Depends(get_db),
):
    get_or_404(db, Trip, trip_id)
    query = select(Place).where(Place.trip_id == trip_id)
    if visited is not None:
        query = query.where(Place.visited == visited)
    if category is not None:
        query = query.where(Place.category == category.value)
    return db.scalars(query.order_by(Place.priority.desc(), Place.name)).all()


@router.post("/trips/{trip_id}/places", response_model=PlaceRead, status_code=201)
def create_place(trip_id: int, payload: PlaceCreate, db: Session = Depends(get_db)):
    get_or_404(db, Trip, trip_id)
    place = Place(trip_id=trip_id)
    apply_updates(place, payload.model_dump())
    db.add(place)
    db.commit()
    db.refresh(place)
    return place


@router.patch("/places/{place_id}", response_model=PlaceRead)
def update_place(place_id: int, payload: PlaceUpdate, db: Session = Depends(get_db)):
    place = get_or_404(db, Place, place_id)
    apply_updates(place, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(place)
    return place


@router.delete("/places/{place_id}", status_code=204)
def delete_place(place_id: int, db: Session = Depends(get_db)):
    place = get_or_404(db, Place, place_id)
    db.delete(place)
    db.commit()
