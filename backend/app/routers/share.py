"""Enlace público de solo lectura de un viaje.

Mismo patrón que el feed .ics: el token ES la llave, así que estas rutas viven
en un router aparte, exento de la sesión de la app (y hay que dejarlo exento
también en la auth del reverse proxy). Lo que sale por aquí lo decide
`schemas/share.py`, campo a campo.
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import CurrentUser
from ..db import get_db
from ..models import Booking, ItineraryItem, Place, Trip
from ..schemas.share import (
    SHARE_SCOPES,
    PublicBooking,
    PublicItineraryItem,
    PublicPlace,
    PublicTraveler,
    PublicTrip,
    ShareState,
    ShareUpdate,
)
from ..services import files
from .common import ensure_trip_member

router = APIRouter(tags=["share"])
# sin sesión: la llave es el token
public_router = APIRouter(tags=["share"])


def _clean_scopes(scopes: list[str]) -> list[str]:
    """Solo secciones conocidas, sin repetir y en orden fijo."""
    wanted = {s.strip().lower() for s in scopes}
    unknown = wanted - set(SHARE_SCOPES)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Secciones desconocidas: {sorted(unknown)}")
    return [scope for scope in SHARE_SCOPES if scope in wanted]


def _state(trip: Trip) -> ShareState:
    return ShareState(token=trip.share_token, scopes=list(trip.share_scopes or []))


@router.put("/trips/{trip_id}/share", response_model=ShareState)
def start_sharing(
    trip_id: int, payload: ShareUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    """Comparte el viaje (o cambia qué secciones se ven). No rota el token: el
    enlace ya repartido sigue valiendo."""
    trip = ensure_trip_member(db, user, trip_id)
    trip.share_scopes = _clean_scopes(payload.scopes)
    if not trip.share_token:
        trip.share_token = secrets.token_urlsafe(24)
    db.commit()
    return _state(trip)


@router.post("/trips/{trip_id}/share/rotate", response_model=ShareState)
def rotate_share_token(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    """Nueva llave: el enlace anterior deja de funcionar al instante."""
    trip = ensure_trip_member(db, user, trip_id)
    if not trip.share_token:
        raise HTTPException(status_code=404, detail="Este viaje no está compartido")
    trip.share_token = secrets.token_urlsafe(24)
    db.commit()
    return _state(trip)


@router.delete("/trips/{trip_id}/share", response_model=ShareState)
def stop_sharing(trip_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    trip = ensure_trip_member(db, user, trip_id)
    trip.share_token = None
    trip.share_scopes = []
    db.commit()
    return _state(trip)


def _shared_trip(db: Session, token: str) -> Trip:
    # mismo 404 para token inexistente y para viaje descompartido: nada que sondear
    trip = db.scalar(select(Trip).where(Trip.share_token == token)) if token else None
    if trip is None:
        raise HTTPException(status_code=404, detail="Enlace no válido o caducado")
    return trip


@public_router.get("/public/trips/{token}", response_model=PublicTrip)
def public_trip(token: str, db: Session = Depends(get_db)):
    trip = _shared_trip(db, token)
    scopes = list(trip.share_scopes or [])

    places: list[PublicPlace] = []
    if "map" in scopes:
        rows = db.scalars(
            select(Place).where(Place.trip_id == trip.id).order_by(Place.id)
        ).all()
        places = [
            PublicPlace(
                id=p.id,
                name=p.name,
                category=p.category,
                address=p.address,
                lat=p.lat,
                lon=p.lon,
                url=p.url,
            )
            for p in rows
        ]

    itinerary: list[PublicItineraryItem] = []
    if "itinerary" in scopes:
        rows = db.scalars(
            select(ItineraryItem)
            .where(ItineraryItem.trip_id == trip.id)
            .order_by(ItineraryItem.day, ItineraryItem.order_index, ItineraryItem.id)
        ).all()
        itinerary = [
            PublicItineraryItem(
                id=i.id,
                day=i.day,
                end_day=i.end_day,
                start_time=i.start_time,
                end_time=i.end_time,
                order_index=i.order_index,
                title=i.title,
                notes=i.notes,
                place_id=i.place_id,
                booking_id=i.booking_id,
            )
            for i in rows
        ]

    bookings: list[PublicBooking] = []
    if "bookings" in scopes:
        rows = db.scalars(
            select(Booking).where(Booking.trip_id == trip.id).order_by(Booking.start_dt, Booking.id)
        ).all()
        bookings = [
            PublicBooking(
                id=b.id,
                type=b.type,
                title=b.title,
                provider=b.provider,
                start_dt=b.start_dt,
                end_dt=b.end_dt,
                origin=b.origin,
                destination=b.destination,
                address=b.address,
                lat=b.lat,
                lon=b.lon,
                place_id=b.place_id,
            )
            for b in rows
        ]

    return PublicTrip(
        name=trip.name,
        countries=list(trip.countries or []),
        start_date=trip.start_date,
        end_date=trip.end_date,
        status=trip.status,
        notes=trip.notes,
        album_url=trip.album_url,
        # la portada se sirve por el mismo token, no por el id del viaje
        cover_url=f"/api/v1/public/trips/{token}/cover?v={trip.cover_image}"
        if trip.cover_image
        else None,
        travelers=[PublicTraveler(name=t.name, color=t.color) for t in trip.travelers],
        scopes=scopes,
        places=places,
        itinerary=itinerary,
        bookings=bookings,
    )


@public_router.get("/public/trips/{token}/cover", include_in_schema=False)
def public_cover(token: str, db: Session = Depends(get_db)):
    trip = _shared_trip(db, token)
    if not trip.cover_image:
        raise HTTPException(status_code=404, detail="Sin portada")
    try:
        path = files.resolve_stored_file(trip.id, trip.cover_image)
    except files.FileValidationError as exc:
        raise HTTPException(status_code=404, detail="Sin portada") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sin portada")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})
