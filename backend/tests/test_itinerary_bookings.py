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
