from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Expense, Trip, WorldPlace


def sync_world_places(db: Session) -> None:
    """Deriva entradas del diario mundial a partir de los viajes (idempotente).

    - Países de viajes TERMINADOS (estado derivado de fechas, así que un viaje
      antiguo añadido a posteriori entra solo).
    - Sitios de viajes marcados como visitados, o enlazados a algún gasto
      (si hubo gasto, se estuvo allí).

    Las entradas derivadas se marcan auto=True; si el usuario las borra se
    ocultan (hidden) para no reaparecer en el siguiente sync.
    """
    world = db.scalars(select(WorldPlace)).all()
    known_codes = {w.country_code for w in world if w.kind == "country" and w.country_code}
    known_trip_place_ids = {w.trip_place_id for w in world if w.trip_place_id is not None}
    expense_place_ids = set(
        db.scalars(select(Expense.place_id).where(Expense.place_id.is_not(None)))
    )

    changed = False
    for trip in db.scalars(select(Trip)):
        if trip.status == "done":
            for code in trip.countries or []:
                if code in known_codes:
                    continue
                # el nombre en español lo resuelve el frontend a partir del código
                db.add(
                    WorldPlace(
                        name=code, kind="country", country_code=code,
                        auto=True, origin=trip.name,
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
                    name=place.name, kind=kind, country_code=place_country,
                    lat=place.lat, lon=place.lon,
                    auto=True, origin=trip.name, trip_place_id=place.id,
                )
            )
            known_trip_place_ids.add(place.id)
            changed = True

    if changed:
        db.commit()
