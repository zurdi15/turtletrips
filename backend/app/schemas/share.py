"""Contrato del enlace público de solo lectura.

⚠️ Estos modelos son la ÚNICA frontera entre el viaje y cualquiera que tenga la
URL: se listan campo a campo a propósito, nunca con `from_attributes` sobre la
entidad entera. Si mañana `Booking` gana una columna con el número de tarjeta,
aquí no aparece sola. Lo que NO sale, y por qué:

  · dinero (gastos, saldos, presupuesto, fondo común, coste y pagador de las
    reservas): el enlace se reenvía por WhatsApp, no es una cuenta compartida
  · códigos de reserva y números de vuelo: con ellos se gestiona (o se cancela)
    una reserva ajena
  · notas privadas de los sitios, `visited`, `priority`, el diario del día y sus
    postales: son el cuaderno de quien viaja, no el folleto
  · ids, avatares y familia de los viajeros: identifican cuentas de la instancia
"""

from datetime import date, datetime, time

from pydantic import BaseModel

from ..models import TripStatus

# secciones que puede llevar el enlace; `balances` queda para la fase 7
SHARE_SCOPES = ("itinerary", "bookings", "map")


class PublicTraveler(BaseModel):
    """Quién viaja: solo lo que sale en un chip de la interfaz."""

    name: str
    color: str | None


class PublicPlace(BaseModel):
    id: int  # contador local, no una llave: hace falta para enlazar el itinerario
    name: str
    category: str
    address: str | None
    lat: float | None
    lon: float | None
    url: str | None


class PublicItineraryItem(BaseModel):
    id: int
    day: date
    end_day: date | None
    start_time: time | None
    end_time: time | None
    order_index: int
    title: str
    notes: str | None
    place_id: int | None
    booking_id: int | None


class PublicBooking(BaseModel):
    id: int
    type: str
    title: str
    provider: str | None
    start_dt: datetime | None
    end_dt: datetime | None
    origin: str | None
    destination: str | None
    address: str | None
    lat: float | None
    lon: float | None
    place_id: int | None


class PublicTrip(BaseModel):
    name: str
    countries: list[str]
    start_date: date | None
    end_date: date | None
    status: TripStatus
    notes: str | None
    album_url: str | None
    cover_url: str | None
    # encuadre de la portada: sin él, el enlace público recorta la foto por el
    # centro y enseña otra cosa que la app
    cover_focus_x: float
    cover_focus_y: float
    travelers: list[PublicTraveler] = []
    scopes: list[str] = []
    places: list[PublicPlace] = []
    itinerary: list[PublicItineraryItem] = []
    bookings: list[PublicBooking] = []


class ShareState(BaseModel):
    """Estado del enlace para quien lo administra desde la app."""

    token: str | None
    scopes: list[str]


class ShareUpdate(BaseModel):
    scopes: list[str] = list(SHARE_SCOPES)
