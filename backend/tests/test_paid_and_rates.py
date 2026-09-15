from datetime import date
from decimal import Decimal

import pytest

from app.services import rates


def _trip(client, travelers: int = 2) -> dict:
    trip = client.post("/api/v1/trips", json={"name": "Vietnam"}).json()
    ids = [t["id"] for t in trip["travelers"]]
    for i in range(travelers - len(ids)):
        traveler = client.post("/api/v1/travelers", json={"name": f"Viajero {i}"}).json()
        client.post(f"/api/v1/trips/{trip['id']}/travelers/{traveler['id']}")
        ids.append(traveler["id"])
    return {"id": trip["id"], "travelers": ids}


def test_expense_paid_defaults_true_and_toggles(client):
    trip = _trip(client)
    exp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-10-01", "description": "Hotel", "amount": 100},
    ).json()
    assert exp["paid"] is True

    resp = client.patch(f"/api/v1/expenses/{exp['id']}", json={"paid": False})
    assert resp.status_code == 200
    assert resp.json()["paid"] is False
    # el patch parcial no lo toca
    assert client.patch(f"/api/v1/expenses/{exp['id']}", json={"notes": "x"}).json()["paid"] is False

    created_unpaid = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-10-02", "description": "Tour", "amount": 40, "paid": False},
    ).json()
    assert created_unpaid["paid"] is False


def test_unpaid_expenses_count_in_totals_but_not_in_balances(client):
    trip = _trip(client)
    payer = trip["travelers"][0]
    client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-10-01", "description": "Cena", "amount": 50, "paid_by_id": payer},
    )
    client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2026-10-02",
            "description": "Hotel in situ",
            "amount": 200,
            "paid_by_id": payer,
            "paid": False,
        },
    )
    balances = client.get(f"/api/v1/trips/{trip['id']}/balances").json()
    assert balances["pending_count"] == 1
    assert balances["pending_total_base"] == 200.0
    by_id = {b["traveler_id"]: b for b in balances["balances"]}
    # solo la cena genera deuda: 50 pagados, 25 debidos
    assert by_id[payer]["paid_base"] == 50.0
    assert by_id[payer]["net_base"] == 25.0

    summary = client.get(f"/api/v1/trips/{trip['id']}/summary").json()
    assert summary["total_base"] == 250.0


@pytest.mark.anyio
async def test_get_rate_falls_back_to_second_provider(db_session, monkeypatch):
    calls: list[str] = []

    async def no_frankfurter(base, quote, day):
        calls.append("frankfurter")
        return None

    async def fallback(base, quote, day):
        calls.append("fallback")
        assert (base, quote) == ("EUR", "VND")
        return Decimal("30174.42")

    monkeypatch.setattr(rates, "_fetch_frankfurter", no_frankfurter)
    monkeypatch.setattr(rates, "_fetch_fallback", fallback)

    rate, source = await rates.get_rate(db_session, "eur", "vnd", date(2026, 9, 10))
    assert rate == Decimal("30174.42")
    assert source == "api"
    assert calls == ["frankfurter", "fallback"]

    # segunda vez: de la caché, sin tocar ningún proveedor
    rate, source = await rates.get_rate(db_session, "EUR", "VND", date(2026, 9, 10))
    assert source == "cache"
    assert calls == ["frankfurter", "fallback"]


@pytest.mark.anyio
async def test_get_rate_unavailable_when_both_providers_fail(db_session, monkeypatch):
    async def none(base, quote, day):
        return None

    monkeypatch.setattr(rates, "_fetch_frankfurter", none)
    monkeypatch.setattr(rates, "_fetch_fallback", none)
    with pytest.raises(rates.RateUnavailableError):
        await rates.get_rate(db_session, "EUR", "XXX", date(2026, 9, 10))


@pytest.fixture
def anyio_backend():
    return "asyncio"
