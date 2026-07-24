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


def test_booking_create_expense(client, trip):
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

    # el gasto generado hereda el sitio de la reserva
    expense = client.post(f"/api/v1/bookings/{booking['id']}/create-expense").json()
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
    expense = client.post(f"/api/v1/bookings/{booking['id']}/create-expense").json()

    # segundo intento: la reserva ya tiene gasto enlazado
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

    expense = client.post(f"/api/v1/bookings/{booking['id']}/create-expense").json()
    assert expense["paid_by_id"] == traveler["id"]
    assert expense["paid_by_common"] is False

    # marcar fondo común suelta al pagador (excluyentes)
    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}", json={"paid_by_common": True}
    ).json()
    assert updated["paid_by_common"] is True
    assert updated["paid_by_id"] is None


def test_booking_create_expense_requires_cost(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "activity", "title": "Teamlab"},
    ).json()
    resp = client.post(f"/api/v1/bookings/{booking['id']}/create-expense")
    assert resp.status_code == 400


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
