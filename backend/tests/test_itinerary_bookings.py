def _linked_expense(client, trip_id: int, booking_id: int) -> dict:
    """El gasto que la reserva crea automáticamente al tener coste."""
    return next(
        e
        for e in client.get(f"/api/v1/trips/{trip_id}/expenses").json()
        if e["booking_id"] == booking_id
    )


def _block_rates(monkeypatch):
    """Simula estar sin red: cualquier tasa no-trivial falla (determinista)."""
    from app.services.rates import RateUnavailableError

    async def _offline(*args, **kwargs):
        raise RateUnavailableError("offline")

    monkeypatch.setattr("app.services.rates.get_rate", _offline)


def test_itinerary_crud_and_reorder(client, trip):
    trip_id = trip["id"]
    a = client.post(
        f"/api/v1/trips/{trip_id}/itinerary",
        json={"day": "2026-04-01", "title": "Fushimi Inari", "order_index": 0},
    ).json()
    b = client.post(
        f"/api/v1/trips/{trip_id}/itinerary",
        json={"day": "2026-04-01", "title": "Cena en Pontocho", "order_index": 1},
    ).json()

    items = client.get(f"/api/v1/trips/{trip_id}/itinerary").json()
    assert [i["title"] for i in items] == ["Fushimi Inari", "Cena en Pontocho"]

    # mover b al día siguiente y a después
    resp = client.post(
        "/api/v1/itinerary/reorder",
        json={"items": [
            {"id": b["id"], "day": "2026-04-02", "order_index": 0},
            {"id": a["id"], "day": "2026-04-02", "order_index": 1},
        ]},
    )
    assert resp.status_code == 204
    items = client.get(f"/api/v1/trips/{trip_id}/itinerary").json()
    assert [(i["title"], i["day"]) for i in items] == [
        ("Cena en Pontocho", "2026-04-02"),
        ("Fushimi Inari", "2026-04-02"),
    ]


def test_itinerary_multi_day_range(client, trip):
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/itinerary",
        json={"day": "2026-04-01", "end_day": "2026-04-04", "title": "Estancia en Kioto"},
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["end_day"] == "2026-04-04"

    resp = client.patch(f"/api/v1/itinerary/{item['id']}", json={"end_day": "2026-04-05"})
    assert resp.json()["end_day"] == "2026-04-05"


def test_itinerary_link_validation(client, trip):
    other = client.post("/api/v1/trips", json={"name": "Otro", "destination": "Y"}).json()
    place = client.post(
        f"/api/v1/trips/{other['id']}/places", json={"name": "Torre Eiffel"}
    ).json()

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/itinerary",
        json={"day": "2026-04-01", "title": "Visita", "place_id": place["id"]},
    )
    assert resp.status_code == 400


def test_booking_create_expense(client, trip, monkeypatch):
    # sin red: la autocreación en moneda extranjera se salta (best-effort)
    # y el gasto se genera a mano aportando la tasa
    _block_rates(monkeypatch)
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "hotel", "title": "Hotel Gracery", "cost_amount": "54000",
            "cost_currency": "JPY", "start_dt": "2026-04-01T15:00:00",
        },
    ).json()

    resp = client.post(
        f"/api/v1/bookings/{booking['id']}/create-expense",
        json={"exchange_rate": "0.006"},
    )
    assert resp.status_code == 201
    expense = resp.json()
    assert expense["category"] == "Alojamiento"
    assert expense["description"] == "Hotel Gracery"
    assert expense["day"] == "2026-04-01"
    assert expense["amount_base"] == 324.0
    assert expense["booking_id"] == booking["id"]


def test_booking_links_place(client, trip):
    # sin sitios previos: crea el sitio (lodging) y lo enlaza
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "hotel", "title": "Hotel Gracery", "address": "Kabukicho, Tokio",
            "lat": 35.6955, "lon": 139.7022, "cost_amount": "90", "cost_currency": "EUR",
        },
    ).json()
    places = client.get(f"/api/v1/trips/{trip['id']}/places").json()
    assert len(places) == 1
    assert places[0]["name"] == "Hotel Gracery"
    assert places[0]["category"] == "lodging"
    assert places[0]["address"] == "Kabukicho, Tokio"
    assert booking["place_id"] == places[0]["id"]

    # otra reserva pegada al mismo sitio lo reutiliza, no duplica
    other = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "activity", "title": "Cena cerca", "lat": 35.6956, "lon": 139.7023},
    ).json()
    assert other["place_id"] == places[0]["id"]
    assert len(client.get(f"/api/v1/trips/{trip['id']}/places").json()) == 1

    # el gasto autogenerado hereda el sitio de la reserva
    expense = _linked_expense(client, trip["id"], booking["id"])
    assert expense["place_id"] == places[0]["id"]

    # transporte sin coordenadas: ni sitio nuevo ni enlace
    flight = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelo", "origin": "MAD", "destination": "NRT"},
    ).json()
    assert flight["place_id"] is None
    assert len(client.get(f"/api/v1/trips/{trip['id']}/places").json()) == 1


def test_booking_links_nearby_city(client, trip):
    city = client.post(
        f"/api/v1/trips/{trip['id']}/places",
        json={"name": "Tokio", "category": "city", "lat": 35.6812, "lon": 139.7671},
    ).json()
    # a ~7 km del centro: dentro del radio de captura de la ciudad
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "hotel", "title": "Hotel en Shinjuku", "lat": 35.6955, "lon": 139.7022},
    ).json()
    assert booking["place_id"] == city["id"]
    assert len(client.get(f"/api/v1/trips/{trip['id']}/places").json()) == 1

    # editar las coordenadas fuera de la ciudad re-enlaza (crea sitio nuevo)
    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}", json={"lat": 34.6937, "lon": 135.5023}
    ).json()
    assert updated["place_id"] != city["id"]
    assert len(client.get(f"/api/v1/trips/{trip['id']}/places").json()) == 2


def test_booking_create_expense_only_once(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "hotel", "title": "Hotel", "cost_amount": "100", "cost_currency": "EUR"},
    ).json()
    # el gasto nace solo con la reserva; el endpoint manual rechaza duplicar
    expense = _linked_expense(client, trip["id"], booking["id"])
    resp = client.post(f"/api/v1/bookings/{booking['id']}/create-expense")
    assert resp.status_code == 400
    assert "ya tiene un gasto" in resp.json()["detail"]

    # borrar el gasto no toca la reserva y permite regenerarlo
    assert client.delete(f"/api/v1/expenses/{expense['id']}").status_code == 204
    remaining = client.get(f"/api/v1/trips/{trip['id']}/bookings").json()
    assert [b["id"] for b in remaining] == [booking["id"]]
    resp = client.post(f"/api/v1/bookings/{booking['id']}/create-expense")
    assert resp.status_code == 201


def test_booking_payer_inherited_by_expense(client, trip):
    from conftest import add_traveler

    traveler = add_traveler(client, trip["id"], "Ana")

    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "hotel", "title": "Hotel", "cost_amount": "80",
            "cost_currency": "EUR", "paid_by_id": traveler["id"],
        },
    ).json()
    assert booking["paid_by_id"] == traveler["id"]
    assert booking["paid_by_common"] is False

    expense = _linked_expense(client, trip["id"], booking["id"])
    assert expense["paid_by_id"] == traveler["id"]
    assert expense["paid_by_common"] is False

    # marcar fondo común suelta al pagador (excluyentes)
    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}", json={"paid_by_common": True}
    ).json()
    assert updated["paid_by_common"] is True
    assert updated["paid_by_id"] is None


def test_booking_expense_two_way_sync(client, trip):
    from conftest import add_traveler

    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "hotel", "title": "Hotel A", "cost_amount": "100",
            "cost_currency": "EUR", "start_dt": "2026-04-01T15:00:00",
            "paid_by_id": ana["id"],
        },
    ).json()
    expense = _linked_expense(client, trip["id"], booking["id"])

    # reserva → gasto: título, fecha, importe y pagador se espejan
    client.patch(
        f"/api/v1/bookings/{booking['id']}",
        json={
            "title": "Hotel B", "cost_amount": "120",
            "start_dt": "2026-04-02T15:00:00", "paid_by_id": luis["id"],
        },
    )
    synced = next(
        e for e in client.get(f"/api/v1/trips/{trip['id']}/expenses").json()
        if e["id"] == expense["id"]
    )
    assert synced["description"] == "Hotel B"
    assert synced["day"] == "2026-04-02"
    assert synced["amount"] == 120.0
    assert synced["amount_base"] == 120.0
    assert synced["paid_by_id"] == luis["id"]

    # gasto → reserva: importe y pagador vuelven a la reserva
    client.patch(
        f"/api/v1/expenses/{expense['id']}",
        json={"amount": "80", "paid_by_common": True},
    )
    synced_booking = next(
        b for b in client.get(f"/api/v1/trips/{trip['id']}/bookings").json()
        if b["id"] == booking["id"]
    )
    assert synced_booking["cost_amount"] == 80.0
    assert synced_booking["paid_by_common"] is True
    assert synced_booking["paid_by_id"] is None


def test_expense_day_moves_booking_dates(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "hotel", "title": "Hotel", "cost_amount": "100",
            "cost_currency": "EUR", "start_dt": "2026-04-01T15:00:00",
            "end_dt": "2026-04-03T11:00:00",
        },
    ).json()
    expense = _linked_expense(client, trip["id"], booking["id"])
    assert expense["day"] == "2026-04-01"

    # mover el día del gasto desplaza entrada Y salida (misma duración y horas)
    client.patch(f"/api/v1/expenses/{expense['id']}", json={"day": "2026-04-05"})
    moved = next(
        b for b in client.get(f"/api/v1/trips/{trip['id']}/bookings").json()
        if b["id"] == booking["id"]
    )
    assert moved["start_dt"] == "2026-04-05T15:00:00"
    assert moved["end_dt"] == "2026-04-07T11:00:00"

    # y la reserva sigue proyectando su entrada sobre el gasto
    client.patch(f"/api/v1/bookings/{booking['id']}", json={"start_dt": "2026-04-10T15:00:00"})
    synced = next(
        e for e in client.get(f"/api/v1/trips/{trip['id']}/expenses").json()
        if e["id"] == expense["id"]
    )
    assert synced["day"] == "2026-04-10"


def test_booking_create_expense_requires_cost(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "activity", "title": "Teamlab"},
    ).json()
    resp = client.post(f"/api/v1/bookings/{booking['id']}/create-expense")
    assert resp.status_code == 400


def test_booking_auto_expense_when_cost_added(client, trip):
    # sin coste no hay gasto...
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "hotel", "title": "Hotel"},
    ).json()
    assert client.get(f"/api/v1/trips/{trip['id']}/expenses").json() == []

    # ...y al estrenar coste el gasto aparece solo
    client.patch(
        f"/api/v1/bookings/{booking['id']}",
        json={"cost_amount": "50", "cost_currency": "EUR"},
    )
    expense = _linked_expense(client, trip["id"], booking["id"])
    assert expense["amount"] == 50.0
    assert expense["description"] == "Hotel"


def test_places_filters(client, trip):
    trip_id = trip["id"]
    client.post(
        f"/api/v1/trips/{trip_id}/places",
        json={"name": "Kinkakuji", "category": "sight", "priority": 1},
    )
    client.post(
        f"/api/v1/trips/{trip_id}/places",
        json={"name": "Ichiran", "category": "food", "visited": True},
    )

    assert len(client.get(f"/api/v1/trips/{trip_id}/places").json()) == 2
    only_food = client.get(f"/api/v1/trips/{trip_id}/places", params={"category": "food"}).json()
    assert [p["name"] for p in only_food] == ["Ichiran"]
    pending = client.get(f"/api/v1/trips/{trip_id}/places", params={"visited": "false"}).json()
    assert [p["name"] for p in pending] == ["Kinkakuji"]
