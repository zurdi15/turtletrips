import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..auth import CurrentUser
from ..config import get_settings
from ..db import get_db
from ..models import Traveler, Trip, trip_travelers
from ..schemas.misc import TripSummary
from ..schemas.trip import TripCreate, TripRead, TripUpdate, TravelerRead
from ..services import files
from ..services.summary import trip_summary
from .common import (
    ensure_trip_member,
    get_or_404,
    require_family,
    save_new,
    save_updates,
)

router = APIRouter(tags=["trips"])


def _resolve_travelers(db: Session, ids: list[int]) -> list[Traveler]:
    """Viajeros por id (dedup, conserva orden); 404 si alguno no existe."""
    return [get_or_404(db, Traveler, tid) for tid in dict.fromkeys(ids)]


def _ensure_has_account_traveler(travelers: list[Traveler]) -> None:
    """Evita dejar el viaje huérfano: nadie con cuenta = nadie podría verlo."""
    if not any(t.has_user for t in travelers):
        raise HTTPException(
            status_code=409,
            detail="El viaje debe conservar al menos un viajero con cuenta",
        )


@router.get("/trips", response_model=list[TripRead])
def list_trips(user: CurrentUser, db: Session = Depends(get_db)):
    query = (
        select(Trip)
        .options(selectinload(Trip.travelers))
        .order_by(Trip.start_date.is_(None), Trip.start_date.desc(), Trip.id.desc())
    )
    if not user.is_admin:
        query = query.join(trip_travelers).where(
            trip_travelers.c.traveler_id == user.traveler_id
        )
    return db.scalars(query).all()


@router.post("/trips", response_model=TripRead, status_code=201)
def create_trip(payload: TripCreate, user: CurrentUser, db: Session = Depends(get_db)):
    data = payload.model_dump()
    traveler_ids = data.pop("traveler_ids", None)
    if not data.get("base_currency"):
        data["base_currency"] = get_settings().default_currency
    trip = Trip()
    # el viaje hereda la familia del creador: define sus categorías/plantillas
    trip.family_id = require_family(user)
    travelers = _resolve_travelers(db, traveler_ids) if traveler_ids else []
    # el creador (no admin) siempre queda dentro: si no, no vería su propio viaje
    if not user.is_admin and all(t.id != user.traveler_id for t in travelers):
        travelers.append(get_or_404(db, Traveler, user.traveler_id))
    trip.travelers = travelers
    return save_new(db, trip, data)


@router.get("/trips/{trip_id}", response_model=TripRead)
def get_trip(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    return ensure_trip_member(db, user, trip_id)


@router.patch("/trips/{trip_id}", response_model=TripRead)
def update_trip(
    trip_id: int, payload: TripUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
    data = payload.model_dump(exclude_unset=True)
    if "traveler_ids" in data:
        travelers = _resolve_travelers(db, data.pop("traveler_ids") or [])
        if not user.is_admin:
            _ensure_has_account_traveler(travelers)
        trip.travelers = travelers
    return save_updates(db, trip, data)


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    db.delete(trip)
    db.commit()
    files.delete_trip_files(trip_id)


@router.get("/trips/{trip_id}/summary", response_model=TripSummary)
def get_trip_summary(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    return trip_summary(db, trip)


# --- viajeros del viaje (asociación a la lista global) ---


@router.post("/trips/{trip_id}/travelers/{traveler_id}", response_model=list[TravelerRead])
def add_traveler_to_trip(
    trip_id: int, traveler_id: int, user: CurrentUser, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
    traveler = get_or_404(db, Traveler, traveler_id)
    if traveler not in trip.travelers:
        trip.travelers.append(traveler)
        db.commit()
    return trip.travelers


@router.delete("/trips/{trip_id}/travelers/{traveler_id}", response_model=list[TravelerRead])
def remove_traveler_from_trip(
    trip_id: int, traveler_id: int, user: CurrentUser, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
    traveler = get_or_404(db, Traveler, traveler_id)
    if traveler in trip.travelers:
        if not user.is_admin:
            _ensure_has_account_traveler(
                [t for t in trip.travelers if t.id != traveler_id]
            )
        trip.travelers.remove(traveler)
        db.commit()
    return trip.travelers


# --- foto de portada ---


@router.post("/trips/{trip_id}/cover", response_model=TripRead)
async def upload_cover(
    trip_id: int, file: UploadFile, user: CurrentUser, db: Session = Depends(get_db)
):
    trip = ensure_trip_member(db, user, trip_id)
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
    trip_id: int, payload: CoverFromUrl, user: CurrentUser, db: Session = Depends(get_db)
):
    """Descarga una imagen (buscador online) y la guarda como portada."""
    trip = ensure_trip_member(db, user, trip_id)
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
def get_cover(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
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
def delete_cover(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    if trip.cover_image:
        files.delete_stored_file(trip_id, trip.cover_image)
        trip.cover_image = None
        db.commit()
        db.refresh(trip)
    return trip
