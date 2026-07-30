"""Generación de iCalendar (.ics) para el itinerario de un viaje.

Solo emitimos (no parseamos): VEVENTs sin TZID ni RRULE. Las fechas naive de la
app se publican como all-day (VALUE=DATE) o como hora local flotante, que es la
semántica correcta para un itinerario de viaje (las 09:00 son las 09:00 de
donde estés).
"""

from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Booking, BookingSegment, BookingType, ItineraryItem, Place, Trip

PRODID = "-//Turtle Trips//ES"
UID_DOMAIN = "turtle-trips"

TRANSPORT_LABELS = {
    BookingType.flight.value: "Vuelo",
    BookingType.train.value: "Tren",
    BookingType.bus.value: "Autobús",
    BookingType.ferry.value: "Ferry",
}
BOOKING_LABELS = {
    **TRANSPORT_LABELS,
    BookingType.hotel.value: "Hotel",
    BookingType.car_rental.value: "Coche de alquiler",
    BookingType.activity.value: "Actividad",
}


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Pliega líneas a 75 octetos UTF-8 con continuación CRLF + espacio."""
    if len(line.encode("utf-8")) <= 75:
        return line
    parts: list[str] = []
    current = ""
    limit = 75
    for ch in line:
        if len(current.encode("utf-8")) + len(ch.encode("utf-8")) > limit:
            parts.append(current)
            current = ch
            limit = 74  # las continuaciones llevan un espacio inicial
        else:
            current += ch
    parts.append(current)
    return "\r\n ".join(parts)


def _ics_date(d: date) -> str:
    return d.strftime("%Y%m%d")


def _ics_datetime(d: date, t: time) -> str:
    return f"{_ics_date(d)}T{t.strftime('%H%M%S')}"


def _dtstamp(dt: datetime | None) -> str:
    return (dt or datetime(2000, 1, 1)).strftime("%Y%m%dT%H%M%SZ")


def _item_event(item: ItineraryItem, location: str | None) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:itinerary-{item.id}@{UID_DOMAIN}",
        f"DTSTAMP:{_dtstamp(item.updated_at)}",
    ]
    if item.start_time is None:
        end = (item.end_day or item.day) + timedelta(days=1)  # DTEND exclusivo
        lines.append(f"DTSTART;VALUE=DATE:{_ics_date(item.day)}")
        lines.append(f"DTEND;VALUE=DATE:{_ics_date(end)}")
    else:
        lines.append(f"DTSTART:{_ics_datetime(item.day, item.start_time)}")
        if item.end_time is not None:
            end_day = item.end_day or item.day
            if (end_day, item.end_time) > (item.day, item.start_time):
                lines.append(f"DTEND:{_ics_datetime(end_day, item.end_time)}")
    lines.append(f"SUMMARY:{_escape(item.title)}")
    if item.notes:
        lines.append(f"DESCRIPTION:{_escape(item.notes)}")
    if location:
        lines.append(f"LOCATION:{_escape(location)}")
    lines.append("END:VEVENT")
    return lines


def _booking_summary(booking: Booking) -> str:
    label = BOOKING_LABELS.get(booking.type)
    if booking.type in TRANSPORT_LABELS and booking.origin and booking.destination:
        return f"{label}: {booking.origin} → {booking.destination}"
    return f"{label}: {booking.title}" if label else booking.title


def _booking_description(booking: Booking, extra: str | None = None) -> str:
    return "\n".join(
        part
        for part in (
            f"Proveedor: {booking.provider}" if booking.provider else None,
            f"Código: {booking.confirmation_code}" if booking.confirmation_code else None,
            extra,
            booking.notes,
        )
        if part
    )


def _event_times(start: datetime, end: datetime | None) -> list[str]:
    """DTSTART/DTEND con la heurística all-day (00:00 = sin hora)."""
    all_day = start.time() == time(0, 0) and (end is None or end.time() == time(0, 0))
    if all_day:
        end_date = (end.date() if end else start.date()) + timedelta(days=1)
        return [
            f"DTSTART;VALUE=DATE:{_ics_date(start.date())}",
            f"DTEND;VALUE=DATE:{_ics_date(end_date)}",
        ]
    lines = [f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}"]
    if end is not None and end > start:
        lines.append(f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}")
    return lines


def _booking_event(booking: Booking) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:booking-{booking.id}@{UID_DOMAIN}",
        f"DTSTAMP:{_dtstamp(booking.updated_at)}",
    ]
    lines.extend(_event_times(booking.start_dt, booking.end_dt))
    lines.append(f"SUMMARY:{_escape(_booking_summary(booking))}")
    description = _booking_description(booking)
    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")
    if booking.address:
        lines.append(f"LOCATION:{_escape(booking.address)}")
    lines.append("END:VEVENT")
    return lines


def _segment_event(booking: Booking, seg: BookingSegment) -> list[str]:
    """Un VEVENT por tramo, con sus horas reales; la escala queda como hueco.
    UID por position (los ids de tramo se regeneran al editar la reserva)."""
    label = BOOKING_LABELS.get(booking.type)
    if seg.origin and seg.destination:
        summary = f"{label}: {seg.origin} → {seg.destination}"
    else:
        summary = f"{label}: {booking.title}" if label else booking.title
    lines = [
        "BEGIN:VEVENT",
        f"UID:booking-{booking.id}-seg-{seg.position}@{UID_DOMAIN}",
        f"DTSTAMP:{_dtstamp(seg.updated_at or booking.updated_at)}",
    ]
    lines.extend(_event_times(seg.departure_dt, seg.arrival_dt))
    lines.append(f"SUMMARY:{_escape(summary)}")
    number = f"{label}: {seg.flight_number}" if seg.flight_number and label else None
    description = _booking_description(booking, number)
    if description:
        lines.append(f"DESCRIPTION:{_escape(description)}")
    lines.append("END:VEVENT")
    return lines


def build_calendar(db: Session, trip: Trip, include_bookings: bool = True) -> str:
    items = db.scalars(
        select(ItineraryItem)
        .where(ItineraryItem.trip_id == trip.id)
        .order_by(ItineraryItem.day, ItineraryItem.order_index, ItineraryItem.id)
    ).all()
    bookings_by_id = {
        b.id: b
        for b in db.scalars(select(Booking).where(Booking.trip_id == trip.id))
    }
    places_by_id = {
        p.id: p for p in db.scalars(select(Place).where(Place.trip_id == trip.id))
    }

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(trip.name)}",
    ]
    linked_booking_ids: set[int] = set()
    for item in items:
        if item.booking_id:
            linked_booking_ids.add(item.booking_id)
        place = places_by_id.get(item.place_id) if item.place_id else None
        booking = bookings_by_id.get(item.booking_id) if item.booking_id else None
        location = None
        if place:
            location = place.address or place.name
        elif booking:
            location = booking.address
        lines.extend(_item_event(item, location))

    if include_bookings:
        for booking in bookings_by_id.values():
            if booking.id in linked_booking_ids:
                continue
            dated_segments = [s for s in booking.segments if s.departure_dt is not None]
            if dated_segments:
                for seg in dated_segments:
                    lines.extend(_segment_event(booking, seg))
            elif booking.start_dt is not None:
                lines.extend(_booking_event(booking))

    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"
