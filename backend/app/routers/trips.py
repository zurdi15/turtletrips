from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..db import get_db
from ..models import Traveler, Trip
from ..schemas.misc import TripSummary
from ..schemas.trip import TripCreate, TripRead, TripUpdate, TravelerRead
from ..services import files
from ..services.summary import trip_summary
from .common import delete_by_id, get_or_404, save_new, save_updates

router = APIRouter(tags=["trips"])


@router.get("/trips", response_model=list[TripRead])
def list_trips(db: Session = Depends(get_db)):
    return db.scalars(
        select(Trip)
        .options(selectinload(Trip.travelers))
        .order_by(Trip.start_date.is_(None), Trip.start_date.desc(), Trip.id.desc())
    ).all()


@router.post("/trips", response_model=TripRead, status_code=201)
def create_trip(payload: TripCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if not data.get("base_currency"):
        data["base_currency"] = get_settings().default_currency
    return save_new(db, Trip(), data)


@router.get("/trips/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Trip, trip_id)


@router.patch("/trips/{trip_id}", response_model=TripRead)
def update_trip(trip_id: int, payload: TripUpdate, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    return save_updates(db, trip, payload.model_dump(exclude_unset=True))


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    delete_by_id(db, Trip, trip_id)
    files.delete_trip_files(trip_id)


@router.get("/trips/{trip_id}/summary", response_model=TripSummary)
def get_trip_summary(trip_id: int, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    return trip_summary(db, trip)


# --- viajeros del viaje (asociación a la lista global) ---


@router.post("/trips/{trip_id}/travelers/{traveler_id}", response_model=list[TravelerRead])
def add_traveler_to_trip(trip_id: int, traveler_id: int, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    traveler = get_or_404(db, Traveler, traveler_id)
    if traveler not in trip.travelers:
        trip.travelers.append(traveler)
        db.commit()
    return trip.travelers


@router.delete("/trips/{trip_id}/travelers/{traveler_id}", response_model=list[TravelerRead])
def remove_traveler_from_trip(trip_id: int, traveler_id: int, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    traveler = get_or_404(db, Traveler, traveler_id)
    if traveler in trip.travelers:
        trip.travelers.remove(traveler)
        db.commit()
    return trip.travelers


# --- foto de portada ---


@router.post("/trips/{trip_id}/cover", response_model=TripRead)
async def upload_cover(trip_id: int, file: UploadFile, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="La portada debe ser una imagen")
    try:
        stored_name, _size = await files.save_upload(trip_id, file)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    if trip.cover_image:
        files.delete_stored_file(trip_id, trip.cover_image)
    trip.cover_image = stored_name
    db.commit()
    db.refresh(trip)
    return trip


@router.get("/trips/{trip_id}/cover", include_in_schema=False)
def get_cover(trip_id: int, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    if not trip.cover_image:
        raise HTTPException(status_code=404, detail="Sin portada")
    try:
        path = files.resolve_stored_file(trip_id, trip.cover_image)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Sin portada") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sin portada")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


@router.delete("/trips/{trip_id}/cover", response_model=TripRead)
def delete_cover(trip_id: int, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    if trip.cover_image:
        files.delete_stored_file(trip_id, trip.cover_image)
        trip.cover_image = None
        db.commit()
        db.refresh(trip)
    return trip
