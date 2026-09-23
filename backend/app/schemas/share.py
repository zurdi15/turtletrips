"""Contrato del enlace público de solo lectura.

⚠️ Estos modelos son la ÚNICA frontera entre el viaje y cualquiera que tenga la
URL: se listan campo a campo a propósito, nunca con `from_attributes` sobre la
entidad entera. Si mañana `Booking` gana una columna con el número de tarjeta,
aquí no aparece sola. Lo que NO sale, y por qué:

  · dinero (gastos, saldos, presupuesto, fondo común, coste y pagador de las
    reservas): el enlace se reenvía por WhatsApp, no es una cuenta compartida
  · códigos de reserva (el localizador ES la credencial: con él se gestiona o se
    cancela un vuelo ajeno). El NÚMERO de vuelo sí viaja: va impreso en
    cualquier tarjeta de embarque y es lo que se teclea para seguir el vuelo
  · las notas: ni las del viaje, ni las de las actividades, ni las de los
    sitios. El enlace lleva datos duros (horas, rutas, tiempo), no el cuaderno
  · `visited`, `priority`, el diario del día y sus postales
  · ids y familia de los viajeros: identifican cuentas de la instancia (la FOTO
    sí sale, servida por el token: es la misma cara que ya se ve en el chip)
"""

from datetime import date, datetime, time

from pydantic import BaseModel

from ..models import TripStatus

# secciones que puede llevar el enlace; `balances` queda para la fase 7
SHARE_SCOPES = ("itinerary", "bookings", "map")


class PublicTraveler(BaseModel):
    """Quién viaja: solo lo que sale en un chip de la interfaz.

    La foto viaja por el TOKEN (`/public/trips/{token}/avatars/{fichero}`), no
    por el id del viajero: el enlace nunca dice qué cuentas hay en la instancia.
    """

    name: str
    color: str | None
    avatar_url: str | None = None
    avatar_focus_x: float = 0.5
    avatar_focus_y: float = 0.5


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
    place_id: int | None
    booking_id: int | None


class PublicBookingSegment(BaseModel):
    """Tramo de un transporte: ruta, horas y número de vuelo (sin id: nada lo
    referencia). El localizador de la reserva sigue sin salir."""

    origin: str | None
    destination: str | None
    departure_dt: datetime | None
    arrival_dt: datetime | None
    flight_number: str | None


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
    flight_number: str | None
    segments: list[PublicBookingSegment] = []


class PublicTrip(BaseModel):
    name: str
    countries: list[str]
    start_date: date | None
    end_date: date | None
    status: TripStatus
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
