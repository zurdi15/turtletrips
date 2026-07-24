import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
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


def _resolve_travelers(db: Session, ids: list[int]) -> list[Traveler]:
    """Viajeros por id (dedup, conserva orden); 404 si alguno no existe."""
    return [get_or_404(db, Traveler, tid) for tid in dict.fromkeys(ids)]


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
    traveler_ids = data.pop("traveler_ids", None)
    if not data.get("base_currency"):
        data["base_currency"] = get_settings().default_currency
    trip = Trip()
    if traveler_ids:
        trip.travelers = _resolve_travelers(db, traveler_ids)
    return save_new(db, trip, data)


@router.get("/trips/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, Trip, trip_id)


@router.patch("/trips/{trip_id}", response_model=TripRead)
def update_trip(trip_id: int, payload: TripUpdate, db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    data = payload.model_dump(exclude_unset=True)
    if "traveler_ids" in data:
        trip.travelers = _resolve_travelers(db, data.pop("traveler_ids") or [])
    return save_updates(db, trip, data)


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


class CoverFromUrl(BaseModel):
    url: HttpUrl


_COVER_MIME_SUFFIX = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/trips/{trip_id}/cover-from-url", response_model=TripRead)
async def cover_from_url(
    trip_id: int, payload: CoverFromUrl, db: Session = Depends(get_db)
):
    """Descarga una imagen (buscador online) y la guarda como portada."""
    trip = get_or_404(db, Trip, trip_id)
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                str(payload.url), headers={"User-Agent": "tt-travel-app/0.1 (self-hosted)"}
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"No se pudo descargar la imagen: {exc}"
        ) from exc
    content_type = resp.headers.get("content-type", "").split(";")[0].strip()
    suffix = _COVER_MIME_SUFFIX.get(content_type)
    if suffix is None:
        raise HTTPException(status_code=415, detail="La URL no apunta a una imagen")
    try:
        stored_name = files.save_bytes(trip_id, resp.content, suffix)
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
