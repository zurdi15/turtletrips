from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..schemas.misc import DayForecast
from ..services import weather as weather_service

router = APIRouter(tags=["weather"])


@router.get("/weather", response_model=list[DayForecast])
async def weather(
    lat: float = Query(ge=-90, le=90),
    lon: float = Query(ge=-180, le=180),
    start: date = Query(),
    end: date = Query(),
):
    """Previsión diaria (Open-Meteo) recortada al horizonte disponible.

    Fuera del horizonte (viajes pasados o lejanos) responde lista vacía, no error.
    """
    clamped = weather_service.clamp_forecast_range(start, end)
    if clamped is None:
        return []
    try:
        return await weather_service.forecast(lat, lon, *clamped)
    except weather_service.WeatherError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
