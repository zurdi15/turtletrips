from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Expense, Traveler, Trip, WorldPlace, trip_travelers


def derive_country_visits(
    places: Iterable[WorldPlace],
) -> dict[int, tuple[int, int | None]]:
    """Fecha heredada para los países SIN fecha propia: la visita más antigua
    de sus ciudades/sitios (si estuviste en una ciudad, estuviste en su país).

    Devuelve {id del país: (año, mes)}; se calcula al leer, así sigue al día
    cuando cambian las fechas de las ciudades. Sin mes gana lo menos preciso
    (2015 antes que marzo de 2015: solo consta el año).
    """
    earliest: dict[str, tuple[int, int | None]] = {}
    for place in places:
        if place.kind == "country" or not place.country_code or place.visited_year is None:
            continue
        candidate = (place.visited_year, place.visited_month)
        current = earliest.get(place.country_code)
        if current is None or (candidate[0], candidate[1] or 0) < (current[0], current[1] or 0):
            earliest[place.country_code] = candidate
    return {
        place.id: earliest[place.country_code]
        for place in places
        if place.kind == "country"
        and place.visited_year is None
        and place.country_code
        and place.country_code in earliest
    }


def ensure_country_entry(
    db: Session, family_id: int, country_code: str | None, origin: str | None = None
) -> bool:
    """Añade la entrada de país al diario de la familia si no existe (ni oculta).

    Una ciudad/sitio en el diario implica haber estado en su país. La entrada
    nace SIN fecha a propósito: la hereda de sus ciudades al leerla
    (derive_country_visits), así sigue siendo la más antigua cuando se añaden
    ciudades anteriores. Respeta los borrados del usuario (hidden cuenta como
    existente). No hace commit.
    """
    if not country_code:
        return False
    exists = db.scalar(
        select(WorldPlace).where(
            WorldPlace.family_id == family_id,
            WorldPlace.kind == "country",
            WorldPlace.country_code == country_code,
        )
    )
    if exists:
        return False
    # el nombre en el idioma activo lo resuelve el frontend a partir del código
    db.add(
        WorldPlace(
            family_id=family_id, name=country_code, kind="country",
            country_code=country_code, auto=True, origin=origin,
        )
    )
    return True


def sync_world_places(db: Session, family_id: int) -> None:
    """Deriva el diario mundial de UNA familia a partir de sus viajes (idempotente).

    Cuentan los viajes de la familia (trip.family_id) y aquellos donde participa
    al menos un viajero de la familia (viajes conjuntos con otras familias):
    - Países de viajes TERMINADOS (estado derivado de fechas, así que un viaje
      antiguo añadido a posteriori entra solo).
    - Sitios de viajes marcados como visitados, o enlazados a algún gasto
      (si hubo gasto, se estuvo allí).

    Las entradas derivadas se marcan auto=True; si el usuario las borra se
    ocultan (hidden) para no reaparecer en el siguiente sync.
    """
    world = db.scalars(
        select(WorldPlace).where(WorldPlace.family_id == family_id)
    ).all()
    known_codes = {w.country_code for w in world if w.kind == "country" and w.country_code}
    known_trip_place_ids = {w.trip_place_id for w in world if w.trip_place_id is not None}
    expense_place_ids = set(
        db.scalars(select(Expense.place_id).where(Expense.place_id.is_not(None)))
    )

    family_traveler_ids = select(Traveler.id).where(Traveler.family_id == family_id)
    family_trips = select(Trip).where(
        or_(
            Trip.family_id == family_id,
            Trip.id.in_(
                select(trip_travelers.c.trip_id).where(
                    trip_travelers.c.traveler_id.in_(family_traveler_ids)
                )
            ),
        )
    )

    changed = False
    for trip in db.scalars(family_trips):
        # fecha de visita heredada del viaje: alimenta las estadísticas anuales
        trip_date = trip.end_date or trip.start_date
        visited_year = trip_date.year if trip_date else None
        visited_month = trip_date.month if trip_date else None

        if trip.status == "done":
            for code in trip.countries or []:
                if code in known_codes:
                    continue
                # el nombre lo resuelve el frontend a partir del código
                db.add(
                    WorldPlace(
                        family_id=family_id, name=code, kind="country",
                        country_code=code, auto=True, origin=trip.name,
                        visited_year=visited_year, visited_month=visited_month,
                    )
                )
                known_codes.add(code)
                changed = True

        countries = trip.countries or []
        place_country = countries[0] if len(countries) == 1 else None
        for place in trip.places:
            if place.id in known_trip_place_ids:
                continue
            if not (place.visited or place.id in expense_place_ids):
                continue
            kind = "city" if place.category in ("city", "town") else "place"
            db.add(
                WorldPlace(
                    family_id=family_id, name=place.name, kind=kind,
                    country_code=place_country, lat=place.lat, lon=place.lon,
                    auto=True, origin=trip.name, trip_place_id=place.id,
                    visited_year=visited_year, visited_month=visited_month,
                )
            )
            known_trip_place_ids.add(place.id)
            changed = True
            # estar en una ciudad/sitio implica estar en su país
            if place_country and place_country not in known_codes:
                db.add(
                    WorldPlace(
                        family_id=family_id, name=place_country, kind="country",
                        country_code=place_country, auto=True, origin=trip.name,
                        visited_year=visited_year, visited_month=visited_month,
                    )
                )
                known_codes.add(place_country)

    if changed:
        db.commit()
