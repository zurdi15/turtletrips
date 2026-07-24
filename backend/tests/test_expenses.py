from datetime import date
from decimal import Decimal

from app.models import ExchangeRateCache

from conftest import add_traveler


def _seed_rate(db_session, base, quote, day, rate):
    db_session.add(
        ExchangeRateCache(base=base, quote=quote, day=date.fromisoformat(day), rate=Decimal(rate))
    )
    db_session.commit()


def test_expense_same_currency(client, trip):
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-04-01", "description": "Cena", "amount": "45.20", "category": "Comida"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["currency"] == "EUR"
    assert data["exchange_rate"] == 1
    assert data["amount_base"] == 45.2
    assert data["category"] == "Comida"


def test_expense_foreign_currency_uses_cached_rate(client, trip, db_session):
    _seed_rate(db_session, "JPY", "EUR", "2026-04-02", "0.006")
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-04-02", "description": "Sushi", "amount": "3000", "currency": "JPY"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["exchange_rate"] == 0.006
    assert data["amount_base"] == 18.0


def test_expense_explicit_rate_and_recompute_on_patch(client, trip):
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2026-04-03", "description": "Hotel", "amount": "10000",
            "currency": "JPY", "exchange_rate": "0.0061", "category": "Alojamiento",
        },
    )
    assert resp.status_code == 201
    expense = resp.json()
    assert expense["amount_base"] == 61.0

    resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={"amount": "20000"})
    assert resp.json()["amount_base"] == 122.0


def test_expense_unknown_rate_fails_offline(client, trip, monkeypatch):
    import app.services.rates as rates_service
    from app.services.rates import RateUnavailableError

    async def boom(*args, **kwargs):
        raise RateUnavailableError("sin red")

    # sin cache y sin red -> 400 pidiendo la tasa manual
    monkeypatch.setattr(rates_service, "get_rate", boom)
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-04-04", "description": "Taxi", "amount": "100", "currency": "USD"},
    )
    assert resp.status_code == 400


def test_expense_linked_place(client, trip):
    place = client.post(
        f"/api/v1/trips/{trip['id']}/places", json={"name": "Ichiran", "category": "food"}
    ).json()
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2026-04-01", "description": "Ramen", "amount": "12",
            "category": "Comida", "place_id": place["id"],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["place_id"] == place["id"]

    # sitio de otro viaje -> 400
    other = client.post("/api/v1/trips", json={"name": "Otro"}).json()
    foreign = client.post(
        f"/api/v1/trips/{other['id']}/places", json={"name": "Torre Eiffel"}
    ).json()
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-04-01", "description": "X", "amount": "5", "place_id": foreign["id"]},
    )
    assert resp.status_code == 400


def test_summary(client, trip):
    trip_id = trip["id"]
    traveler = add_traveler(client, trip_id, "Romm")
    client.patch(f"/api/v1/trips/{trip_id}", json={"budget_amount": "1000"})

    client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        json={
            "day": "2026-04-01", "description": "Cena", "amount": "40",
            "category": "Comida", "paid_by_id": traveler["id"],
        },
    )
    client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        json={"day": "2026-04-02", "description": "Museo", "amount": "10", "category": "Entradas"},
    )

    summary = client.get(f"/api/v1/trips/{trip_id}/summary").json()
    assert summary["total_base"] == 50.0
    assert summary["remaining"] == 950.0
    assert summary["expense_count"] == 2
    assert {c["category"]: c["total"] for c in summary["by_category"]} == {
        "Comida": 40.0, "Entradas": 10.0,
    }
    payers = {p["name"]: p["total"] for p in summary["by_payer"]}
    assert payers == {"Romm": 40.0, "Sin asignar": 10.0}
    assert summary["by_day"] == [
        {"day": "2026-04-01", "total": 40.0},
        {"day": "2026-04-02", "total": 10.0},
    ]
