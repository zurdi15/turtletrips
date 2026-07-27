from datetime import date, timedelta

from app.schemas.misc import DayForecast
from app.services.weather import clamp_forecast_range


def test_clamp_forecast_range():
    today = date(2026, 7, 27)
    # viaje pasado o demasiado lejano: fuera del horizonte
    assert clamp_forecast_range(date(2026, 1, 1), date(2026, 1, 10), today) is None
    assert clamp_forecast_range(date(2027, 1, 1), date(2027, 1, 10), today) is None
    # viaje en curso: se recorta a hoy..+15
    assert clamp_forecast_range(date(2026, 7, 20), date(2026, 9, 1), today) == (
        today,
        today + timedelta(days=15),
    )
    # viaje dentro del horizonte: intacto
    assert clamp_forecast_range(date(2026, 7, 28), date(2026, 7, 30), today) == (
        date(2026, 7, 28),
        date(2026, 7, 30),
    )


def test_weather_endpoint(client, monkeypatch):
    async def fake_forecast(lat, lon, start, end):
        assert start >= date.today()
        return [DayForecast(day=start, weather_code=61, t_max=21.5, t_min=12.0, precip_prob=80)]

    monkeypatch.setattr("app.services.weather.forecast", fake_forecast)

    today = date.today().isoformat()
    resp = client.get(f"/api/v1/weather?lat=40.4&lon=-3.7&start={today}&end={today}")
    assert resp.status_code == 200
    assert resp.json()[0]["weather_code"] == 61

    # rango fuera del horizonte: lista vacía sin llamar fuera
    resp = client.get("/api/v1/weather?lat=40.4&lon=-3.7&start=2000-01-01&end=2000-01-05")
    assert resp.json() == []
