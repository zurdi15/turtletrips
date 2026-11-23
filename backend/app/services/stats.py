"""Estadísticas anuales de viaje ("Tu año viajero").

Lógica pura sobre filas ya cargadas: los viajes se reparten entre los años
que tocan (uno que cruza Nochevieja cuenta en ambos), los días se recortan
al año y el gasto se agrupa por el día real de cada gasto y la moneda base
de su viaje (sumar monedas base distintas sería mentir).
"""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from ..models import Booking, Expense, Trip
from ..schemas.misc import CurrencyTotal, YearStats


def _years_of(trip: Trip) -> range:
    end = trip.end_date or trip.start_date
    return range(trip.start_date.year, end.year + 1)


def _days_in_year(trip: Trip, year: int) -> int:
    start = max(trip.start_date, date(year, 1, 1))
    end = min(trip.end_date or trip.start_date, date(year, 12, 31))
    return (end - start).days + 1 if end >= start else 0


def _lodging_allocations(
    expense: Expense, booking_by_id: dict[int, Booking]
) -> list[tuple[date, Decimal]]:
    booking = booking_by_id.get(expense.booking_id) if expense.booking_id is not None else None
    if (
        booking is None
        or booking.type != "hotel"
        or booking.start_dt is None
        or booking.end_dt is None
    ):
        return [(expense.day, Decimal(str(expense.amount_base)))]
    start = booking.start_dt.date()
    nights = max(1, (booking.end_dt.date() - start).days)
    total_cents = int(Decimal(str(expense.amount_base)) * 100)
    base, remainder = divmod(total_cents, nights)
    return [
        (start + timedelta(days=index), Decimal(base + (index < remainder)) / 100)
        for index in range(nights)
    ]


def yearly_stats(
    trips: list[Trip],
    expenses: list[Expense],
    world_countries: list[tuple[int, str]] | None = None,
    bookings: list[Booking] | None = None,
) -> list[YearStats]:
    """`world_countries`: (año, código) del diario mundial — entradas
    retroactivas con fecha de visita que no vienen de ningún viaje de la app."""
    trips_by_year: dict[int, list[Trip]] = defaultdict(list)
    for trip in trips:
        if trip.start_date is None:
            continue  # sin fechas no hay año que contar
        for year in _years_of(trip):
            trips_by_year[year].append(trip)

    extra_by_year: dict[int, set[str]] = defaultdict(set)
    for year, code in world_countries or []:
        extra_by_year[year].add(code)

    # gasto por año real del gasto y moneda base de su viaje
    currency_of = {trip.id: trip.base_currency for trip in trips}
    booking_by_id = {booking.id: booking for booking in bookings or []}
    spent: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for expense in expenses:
        currency = currency_of.get(expense.trip_id)
        if currency is None:
            continue
        for day, amount in _lodging_allocations(expense, booking_by_id):
            spent[day.year][currency] += float(amount)

    seen_countries: set[str] = set()
    results: list[YearStats] = []
    for year in sorted(set(trips_by_year) | set(spent) | set(extra_by_year)):
        year_trips = trips_by_year.get(year, [])
        countries = sorted(
            {code for trip in year_trips for code in (trip.countries or [])}
            | extra_by_year.get(year, set())
        )
        new_countries = [code for code in countries if code not in seen_countries]
        seen_countries.update(countries)
        results.append(
            YearStats(
                year=year,
                trips=len(year_trips),
                days=sum(_days_in_year(trip, year) for trip in year_trips),
                countries=countries,
                new_countries=new_countries,
                spent=[
                    CurrencyTotal(currency=cur, amount=round(total, 2))
                    for cur, total in sorted(spent.get(year, {}).items())
                ],
            )
        )
    return results
