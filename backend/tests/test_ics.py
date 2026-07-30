def _item(client, trip_id, **overrides):
    payload = {"day": "2026-02-10", "title": "Actividad"}
    payload.update(overrides)
    resp = client.post(f"/api/v1/trips/{trip_id}/itinerary", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _booking(client, trip_id, **overrides):
    payload = {"type": "hotel", "title": "Reserva"}
    payload.update(overrides)
    resp = client.post(f"/api/v1/trips/{trip_id}/bookings", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _ics(client, trip_id, query=""):
    resp = client.get(f"/api/v1/trips/{trip_id}/calendar.ics{query}")
    assert resp.status_code == 200
    return resp


def test_all_day_single_and_multi_day(client, trip):
    _item(client, trip["id"], day="2026-02-10", title="Museo")
    _item(client, trip["id"], day="2026-02-11", end_day="2026-02-13", title="Ruta")

    body = _ics(client, trip["id"]).text
    # un día: DTEND exclusivo = día siguiente
    assert "DTSTART;VALUE=DATE:20260210" in body
    assert "DTEND;VALUE=DATE:20260211" in body
    # multi-día: end_day 12 inclusive -> DTEND 13+1? No: end_day=13 -> DTEND=14
    assert "DTSTART;VALUE=DATE:20260211" in body
    assert "DTEND;VALUE=DATE:20260214" in body


def test_timed_event_is_floating(client, trip):
    _item(
        client,
        trip["id"],
        day="2026-02-10",
        title="Cena",
        start_time="09:30:00",
        end_time="11:00:00",
    )
    body = _ics(client, trip["id"]).text
    assert "DTSTART:20260210T093000" in body
    assert "DTEND:20260210T110000" in body
    # hora flotante: sin sufijo Z en DTSTART/DTEND
    for line in body.split("\r\n"):
        if line.startswith(("DTSTART", "DTEND")):
            assert not line.endswith("Z")


def test_escaping_and_folding(client, trip):
    _item(
        client,
        trip["id"],
        title="Cena, sushi; rico",
        notes="línea1\nlínea2 " + "x" * 100,
    )
    body = _ics(client, trip["id"]).text
    assert "SUMMARY:Cena\\, sushi\\; rico" in body
    assert "\\n" in body  # los saltos de línea van escapados
    # plegado a 75 octetos con continuación "CRLF espacio"
    assert "\r\n " in body
    unfolded = body.replace("\r\n ", "")
    assert unfolded.count("BEGIN:VEVENT") == unfolded.count("END:VEVENT") == 1
    for line in body.split("\r\n"):
        assert len(line.encode("utf-8")) <= 76  # 75 + espacio de continuación


def test_flight_booking_summary_and_toggle(client, trip):
    _booking(
        client,
        trip["id"],
        type="flight",
        title="Iberia 6800",
        origin="MAD",
        destination="Tokio",
        start_dt="2026-02-10T08:15:00",
        provider="Iberia",
        confirmation_code="ABC123",
    )
    body = _ics(client, trip["id"]).text
    assert "SUMMARY:Vuelo: MAD → Tokio" in body.replace("\r\n ", "")
    assert "DTSTART:20260210T081500" in body
    unfolded = body.replace("\r\n ", "")
    assert "Proveedor: Iberia" in unfolded
    assert "Código: ABC123" in unfolded

    without = _ics(client, trip["id"], "?bookings=false").text
    assert "BEGIN:VEVENT" not in without


def test_linked_booking_not_duplicated(client, trip):
    booking = _booking(
        client, trip["id"], type="hotel", title="Hotel", start_dt="2026-02-10T00:00:00"
    )
    _item(client, trip["id"], title="Check-in", booking_id=booking["id"])

    body = _ics(client, trip["id"]).text
    assert "UID:itinerary-" in body
    assert f"UID:booking-{booking['id']}@" not in body


def test_all_day_booking_heuristic(client, trip):
    _booking(
        client,
        trip["id"],
        type="hotel",
        title="Ryokan",
        start_dt="2026-02-10T00:00:00",
        end_dt="2026-02-12T00:00:00",
        address="Kioto",
    )
    body = _ics(client, trip["id"]).text
    assert "DTSTART;VALUE=DATE:20260210" in body
    assert "DTEND;VALUE=DATE:20260213" in body  # end_dt inclusivo -> exclusivo +1
    assert "LOCATION:Kioto" in body


def test_segmented_booking_event_per_segment(client, trip):
    booking = _booking(
        client,
        trip["id"],
        type="flight",
        title="Vuelos Japón",
        provider="Qatar Airways",
        confirmation_code="XYZ789",
        segments=[
            {
                "origin": "MAD", "destination": "DOH", "flight_number": "QR150",
                "departure_dt": "2026-02-10T10:00:00", "arrival_dt": "2026-02-10T18:30:00",
            },
            {
                "origin": "DOH", "destination": "NRT", "flight_number": "QR806",
                "departure_dt": "2026-02-10T21:55:00", "arrival_dt": "2026-02-11T13:20:00",
            },
        ],
    )
    unfolded = _ics(client, trip["id"]).text.replace("\r\n ", "")
    # un VEVENT por tramo con UID estable por position, no el agregado
    assert f"UID:booking-{booking['id']}-seg-0@" in unfolded
    assert f"UID:booking-{booking['id']}-seg-1@" in unfolded
    assert f"UID:booking-{booking['id']}@" not in unfolded
    assert "SUMMARY:Vuelo: MAD → DOH" in unfolded
    assert "SUMMARY:Vuelo: DOH → NRT" in unfolded
    assert "DTSTART:20260210T100000" in unfolded
    assert "DTSTART:20260210T215500" in unfolded
    assert "DTEND:20260211T132000" in unfolded
    # la descripción común viaja en cada tramo, con su número de vuelo
    assert "Vuelo: QR150" in unfolded
    assert "Vuelo: QR806" in unfolded
    assert unfolded.count("Proveedor: Qatar Airways") == 2


def test_segmented_all_day_heuristic_per_segment(client, trip):
    _booking(
        client,
        trip["id"],
        type="train",
        title="Tren nocturno",
        segments=[
            {
                "origin": "Osaka", "destination": "Tokio",
                "departure_dt": "2026-02-10T00:00:00", "arrival_dt": "2026-02-11T00:00:00",
            }
        ],
    )
    body = _ics(client, trip["id"]).text
    assert "DTSTART;VALUE=DATE:20260210" in body
    assert "DTEND;VALUE=DATE:20260212" in body  # inclusivo -> exclusivo +1


def test_segmented_linked_booking_not_duplicated(client, trip):
    booking = _booking(
        client,
        trip["id"],
        type="flight",
        title="Vuelo",
        segments=[
            {
                "origin": "MAD", "destination": "NRT",
                "departure_dt": "2026-02-10T10:00:00",
            }
        ],
    )
    _item(client, trip["id"], title="Vuelo de ida", booking_id=booking["id"])
    body = _ics(client, trip["id"]).text
    assert f"UID:booking-{booking['id']}-seg-" not in body


def test_headers_structure_and_404(client, trip):
    _item(client, trip["id"], title="Algo")
    resp = _ics(client, trip["id"])
    assert resp.headers["content-type"].startswith("text/calendar")
    assert 'filename="itinerario-' in resp.headers["content-disposition"]
    body = resp.text
    assert body.startswith("BEGIN:VCALENDAR\r\n")
    assert body.endswith("END:VCALENDAR\r\n")
    assert "X-WR-CALNAME:" in body

    assert client.get("/api/v1/trips/99999/calendar.ics").status_code == 404


def test_ics_subscription_feed(client, trip):
    _item(client, trip["id"], title="Visita")

    # el token es la llave: se genera, sirve el feed y rotar invalida el viejo
    token = client.post(f"/api/v1/trips/{trip['id']}/ics-token").json()["token"]
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["ics_token"] == token

    feed = client.get(f"/api/v1/calendar/{token}.ics")
    assert feed.status_code == 200
    assert feed.headers["content-type"].startswith("text/calendar")
    assert "SUMMARY:Visita" in feed.text

    assert client.get("/api/v1/calendar/invalido.ics").status_code == 404

    rotated = client.post(f"/api/v1/trips/{trip['id']}/ics-token").json()["token"]
    assert rotated != token
    assert client.get(f"/api/v1/calendar/{token}.ics").status_code == 404
    assert client.get(f"/api/v1/calendar/{rotated}.ics").status_code == 200
