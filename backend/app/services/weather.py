import time
from datetime import date, timedelta

import httpx

from ..schemas.misc import DayForecast

_OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
_DAILY_VARS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
_FORECAST_DAYS = 15  # Open-Meteo sirve ~16 días vista
_CACHE_TTL = 3600.0  # el forecast diario no cambia más deprisa
_CACHE_MAX = 100

_cache: dict[str, tuple[float, list[DayForecast]]] = {}


class WeatherError(Exception):
    pass


def clamp_forecast_range(
    start: date, end: date, today: date | None = None
) -> tuple[date, date] | None:
    """Recorta [start, end] a lo que Open-Meteo puede responder (hoy..+15).

    None si el viaje queda fuera del horizonte de previsión.
    """
    today = today or date.today()
    lo = max(start, today)
    hi = min(end, today + timedelta(days=_FORECAST_DAYS))
    if lo > hi:
        return None
    return lo, hi


async def forecast(lat: float, lon: float, start: date, end: date) -> list[DayForecast]:
    # coords redondeadas: puntos cercanos comparten previsión y entrada de cache
    lat, lon = round(lat, 2), round(lon, 2)
    key = f"{lat}:{lon}:{start.isoformat()}:{end.isoformat()}"
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and now - hit[0] < _CACHE_TTL:
        return hit[1]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                _OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": _DAILY_VARS,
                    "timezone": "auto",
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                },
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise WeatherError(f"Error consultando Open-Meteo: {exc}") from exc

    daily = data.get("daily") or {}
    results = [
        DayForecast(
            day=date.fromisoformat(day),
            weather_code=(daily.get("weather_code") or [])[i] or 0,
            t_max=(daily.get("temperature_2m_max") or [])[i],
            t_min=(daily.get("temperature_2m_min") or [])[i],
            precip_prob=(daily.get("precipitation_probability_max") or [None] * len(daily["time"]))[i],
        )
        for i, day in enumerate(daily.get("time") or [])
    ]
    if len(_cache) >= _CACHE_MAX:
        _cache.pop(next(iter(_cache)))
    _cache[key] = (now, results)
    return results
