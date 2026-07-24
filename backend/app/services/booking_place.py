"""Enlace automático reserva → sitio del viaje.

Una reserva con coordenadas se enlaza al sitio existente más cercano para no
duplicar: un POI a menos de ~300 m, o la ciudad/pueblo a cuyo entorno
pertenece. Si no hay candidato, se crea un sitio nuevo con el nombre de la
reserva (categoría "lodging" para hoteles).
"""

import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Booking, BookingType, Place, PlaceCategory

# radios de captura por tipo de sitio
POI_RADIUS_M = 300
TOWN_RADIUS_M = 5_000
CITY_RADIUS_M = 15_000

TRANSPORT_TYPES = {
    BookingType.flight.value,
    BookingType.train.value,
    BookingType.bus.value,
    BookingType.ferry.value,
}


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia haversine en metros."""
    rad = math.pi / 180
    d_lat = (lat2 - lat1) * rad
    d_lon = (lon2 - lon1) * rad
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1 * rad) * math.cos(lat2 * rad) * math.sin(d_lon / 2) ** 2
    )
    return 2 * 6_371_000 * math.asin(math.sqrt(a))


def _capture_radius_m(place: Place) -> float:
    if place.category == PlaceCategory.city.value:
        return CITY_RADIUS_M
    if place.category == PlaceCategory.town.value:
        return TOWN_RADIUS_M
    return POI_RADIUS_M


def ensure_booking_place(db: Session, booking: Booking) -> None:
    """Enlaza la reserva con un sitio (existente o nuevo). No commitea.

    Sin coordenadas (transportes, direcciones sin geocodificar) o con un
    enlace ya presente, no hace nada.
    """
    if booking.lat is None or booking.lon is None or booking.place_id is not None:
        return

    places = db.scalars(select(Place).where(Place.trip_id == booking.trip_id)).all()
    best: Place | None = None
    best_score = math.inf
    for place in places:
        if place.lat is None or place.lon is None:
            continue
        distance = _distance_m(booking.lat, booking.lon, place.lat, place.lon)
        radius = _capture_radius_m(place)
        if distance > radius:
            continue
        # prioriza el POI exacto frente a la ciudad que también captura
        score = distance / radius
        if score < best_score:
            best, best_score = place, score

    if best is None:
        category = (
            PlaceCategory.lodging
            if booking.type == BookingType.hotel.value
            else PlaceCategory.other
        )
        best = Place(
            trip_id=booking.trip_id,
            name=booking.title,
            category=category.value,
            address=booking.address,
            lat=booking.lat,
            lon=booking.lon,
        )
        db.add(best)
        db.flush()

    booking.place_id = best.id
