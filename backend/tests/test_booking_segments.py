"""Tramos de reservas de transporte: agregados derivados, REPLACE y sync."""


def _linked_expense(client, trip_id: int, booking_id: int) -> dict:
    return next(
        e
        for e in client.get(f"/api/v1/trips/{trip_id}/expenses").json()
        if e["booking_id"] == booking_id
    )


ROUND_TRIP = [
    # ida con escala…
    {
        "origin": "MAD", "destination": "DOH", "flight_number": "QR150",
        "departure_dt": "2026-04-01T10:00:00", "arrival_dt": "2026-04-01T18:30:00",
    },
    {
        "origin": "DOH", "destination": "NRT", "flight_number": "QR806",
        "departure_dt": "2026-04-01T21:55:00", "arrival_dt": "2026-04-02T13:20:00",
    },
    # …y vuelta con escala, días después
    {
        "origin": "NRT", "destination": "DOH", "flight_number": "QR807",
        "departure_dt": "2026-04-14T22:00:00", "arrival_dt": "2026-04-15T04:30:00",
    },
    {
        "origin": "DOH", "destination": "MAD", "flight_number": "QR151",
        "departure_dt": "2026-04-15T07:45:00", "arrival_dt": "2026-04-15T13:45:00",
    },
]


def test_create_with_segments_derives_aggregates(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos Japón", "segments": ROUND_TRIP},
    ).json()

    # los campos planos pasan a ser el agregado; el flight_number vive en el tramo
    assert booking["start_dt"] == "2026-04-01T10:00:00"
    assert booking["end_dt"] == "2026-04-15T13:45:00"
    assert booking["origin"] == "MAD"
    assert booking["destination"] == "MAD"
    assert booking["flight_number"] is None
    assert [s["position"] for s in booking["segments"]] == [0, 1, 2, 3]
    assert [s["flight_number"] for s in booking["segments"]] == [
        "QR150", "QR806", "QR807", "QR151",
    ]


def test_unordered_segments_normalized_by_departure(client, trip):
    shuffled = [ROUND_TRIP[2], ROUND_TRIP[0], ROUND_TRIP[3], ROUND_TRIP[1]]
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos", "segments": shuffled},
    ).json()
    assert [s["origin"] for s in booking["segments"]] == ["MAD", "DOH", "NRT", "DOH"]
    assert booking["start_dt"] == "2026-04-01T10:00:00"

    # un tramo sin fecha conserva su orden de payload, al final
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "train",
            "title": "Trenes",
            "segments": [
                {"origin": "Osaka", "destination": "Hiroshima"},
                ROUND_TRIP[0],
            ],
        },
    ).json()
    assert [s["origin"] for s in booking["segments"]] == ["MAD", "Osaka"]


def test_patch_segments_replaces_set(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos", "segments": ROUND_TRIP[:2]},
    ).json()

    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}", json={"segments": ROUND_TRIP[2:]}
    ).json()
    assert len(updated["segments"]) == 2
    assert updated["origin"] == "NRT"
    assert updated["destination"] == "MAD"
    assert updated["start_dt"] == "2026-04-14T22:00:00"


def test_patch_absent_segments_untouched(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos", "segments": ROUND_TRIP},
    ).json()
    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}", json={"provider": "Qatar Airways"}
    ).json()
    assert len(updated["segments"]) == 4
    assert updated["provider"] == "Qatar Airways"


def test_patch_empty_list_clears_segments(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos", "segments": ROUND_TRIP[:2]},
    ).json()
    updated = client.patch(f"/api/v1/bookings/{booking['id']}", json={"segments": []}).json()
    assert updated["segments"] == []
    # los campos planos no se tocan al vaciar (quedan como estaban)
    assert updated["start_dt"] == "2026-04-01T10:00:00"


def test_empty_segments_keeps_hotel_flat_dates(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "hotel", "title": "Hotel Gracery",
            "start_dt": "2026-04-02T15:00:00", "end_dt": "2026-04-06T11:00:00",
        },
    ).json()
    # el form manda segments: [] para los no-transportes: no debe pisar nada
    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}",
        json={"title": "Hotel Gracery Shinjuku", "segments": []},
    ).json()
    assert updated["start_dt"] == "2026-04-02T15:00:00"
    assert updated["end_dt"] == "2026-04-06T11:00:00"
    assert updated["segments"] == []


def test_flat_date_patch_on_segmented_booking_recomputed(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos", "segments": ROUND_TRIP},
    ).json()
    # tocar los campos planos sin mandar segments: los tramos mandan
    updated = client.patch(
        f"/api/v1/bookings/{booking['id']}",
        json={"start_dt": "2026-05-01T00:00:00", "origin": "BCN"},
    ).json()
    assert updated["start_dt"] == "2026-04-01T10:00:00"
    assert updated["origin"] == "MAD"


def test_segment_arrival_before_departure_422(client, trip):
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "flight",
            "title": "Vuelo",
            "segments": [
                {
                    "origin": "MAD", "destination": "DOH",
                    "departure_dt": "2026-04-01T10:00:00",
                    "arrival_dt": "2026-04-01T08:00:00",
                }
            ],
        },
    )
    assert resp.status_code == 422


def test_fully_empty_segments_dropped(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "flight",
            "title": "Vuelo",
            "segments": [ROUND_TRIP[0], {"origin": None, "destination": None}],
        },
    ).json()
    assert len(booking["segments"]) == 1


def test_auto_expense_day_is_first_departure(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "flight", "title": "Vuelos Japón", "segments": ROUND_TRIP,
            "cost_amount": "1200", "cost_currency": "EUR",
        },
    ).json()
    expense = _linked_expense(client, trip["id"], booking["id"])
    assert expense["day"] == "2026-04-01"
    assert expense["category"] == "Vuelos"


def test_expense_day_move_shifts_all_segments(client, trip):
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "flight", "title": "Vuelos Japón", "segments": ROUND_TRIP,
            "cost_amount": "1200", "cost_currency": "EUR",
        },
    ).json()
    expense = _linked_expense(client, trip["id"], booking["id"])

    # mover el día del gasto un día adelante desplaza los 4 tramos en bloque
    client.patch(f"/api/v1/expenses/{expense['id']}", json={"day": "2026-04-02"})
    moved = client.get(f"/api/v1/trips/{trip['id']}/bookings").json()[0]
    assert moved["start_dt"] == "2026-04-02T10:00:00"
    assert moved["end_dt"] == "2026-04-16T13:45:00"
    assert [s["departure_dt"] for s in moved["segments"]] == [
        "2026-04-02T10:00:00",
        "2026-04-02T21:55:00",
        "2026-04-15T22:00:00",
        "2026-04-16T07:45:00",
    ]
    assert moved["segments"][1]["arrival_dt"] == "2026-04-03T13:20:00"


def test_delete_booking_deletes_segments(client, trip, db_session):
    from app.models import BookingSegment

    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={"type": "flight", "title": "Vuelos", "segments": ROUND_TRIP},
    ).json()
    assert client.delete(f"/api/v1/bookings/{booking['id']}").status_code == 204
    from sqlalchemy import select

    assert db_session.scalars(select(BookingSegment)).all() == []
