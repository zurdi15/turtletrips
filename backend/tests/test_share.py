"""Enlace público de solo lectura: qué se ve, qué NO se ve y quién manda."""

import pytest

from conftest import add_traveler, login, make_user

# lo que jamás puede salir por el endpoint público, pase lo que pase
FORBIDDEN_KEYS = (
    "confirmation_code",
    "flight_number",
    "cost_amount",
    "cost_currency",
    "paid_by_id",
    "paid_by_common",
    "budget_amount",
    "base_currency",
    "ics_token",
    "share_token",
    "family_id",
    "avatar_url",
    "visited",
    "priority",
    "debts_settled",
)


@pytest.fixture
def loaded_trip(client, trip):
    """Viaje con un poco de todo: viajero, sitio, actividad, reserva y gasto."""
    add_traveler(client, trip["id"], "Noelia", "#8b5cf6")
    place = client.post(
        f"/api/v1/trips/{trip['id']}/places",
        json={
            "name": "Fushimi Inari",
            "category": "sight",
            "lat": 34.96,
            "lon": 135.77,
            "notes": "Nota privada del sitio",
            "visited": True,
        },
    ).json()
    booking = client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "flight",
            "title": "Madrid → Tokio",
            "provider": "Iberia",
            "confirmation_code": "SECRETO1",
            "flight_number": "IB6800",
            "start_dt": "2026-02-07T10:00:00",
            "origin": "MAD",
            "destination": "HND",
            "cost_amount": 850,
            "cost_currency": "EUR",
            "notes": "Nota privada de la reserva",
        },
    ).json()
    # la vuelta, con escala: los tramos también son parte de la frontera pública
    client.post(
        f"/api/v1/trips/{trip['id']}/bookings",
        json={
            "type": "flight",
            "title": "Tokio → Madrid",
            "segments": [
                {
                    "origin": "HND", "destination": "DOH", "flight_number": "IB9999",
                    "departure_dt": "2026-02-20T22:00:00",
                    "arrival_dt": "2026-02-21T04:30:00",
                },
                {
                    "origin": "DOH", "destination": "MAD", "flight_number": "IB9998",
                    "departure_dt": "2026-02-21T07:45:00",
                    "arrival_dt": "2026-02-21T13:45:00",
                },
            ],
        },
    )
    client.post(
        f"/api/v1/trips/{trip['id']}/itinerary",
        json={
            "day": "2026-02-10",
            "title": "Torii al amanecer",
            "notes": "Salir a las 6",
            "place_id": place["id"],
        },
    )
    client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-02-10", "description": "Cena", "amount": 40, "currency": "EUR"},
    )
    return {"trip": trip, "place": place, "booking": booking}


def share(client, trip_id, scopes=None):
    payload = {"scopes": scopes} if scopes is not None else {}
    resp = client.put(f"/api/v1/trips/{trip_id}/share", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_share_creates_token_and_defaults_to_all_scopes(client, trip):
    state = share(client, trip["id"])
    assert state["token"]
    assert state["scopes"] == ["itinerary", "bookings", "map"]
    # el viaje lo cuenta en su propia lectura (de ahí tira el diálogo)
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["share_token"] == state["token"]


def test_public_trip_is_readable_without_session(anon, client, loaded_trip):
    token = share(client, loaded_trip["trip"]["id"])["token"]
    resp = anon.get(f"/api/v1/public/trips/{token}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Japón 2026"
    assert data["countries"] == ["JP"]
    assert data["travelers"] == [{"name": "Noelia", "color": "#8b5cf6"}]
    assert data["places"][0]["name"] == "Fushimi Inari"
    assert data["itinerary"][0]["title"] == "Torii al amanecer"
    assert data["bookings"][0]["origin"] == "MAD"


def test_public_trip_never_leaks_private_fields(anon, client, loaded_trip):
    token = share(client, loaded_trip["trip"]["id"])["token"]
    body = anon.get(f"/api/v1/public/trips/{token}").text
    for key in FORBIDDEN_KEYS:
        assert key not in body, f"el enlace público filtra {key}"
    # ni los valores, no solo los nombres de campo (IB9999/IB9998 viven en tramos)
    for value in ("SECRETO1", "IB6800", "IB9999", "IB9998", "850", "Nota privada"):
        assert value not in body, f"el enlace público filtra {value!r}"


def test_public_booking_segments_expose_route_and_times(anon, client, loaded_trip):
    token = share(client, loaded_trip["trip"]["id"])["token"]
    data = anon.get(f"/api/v1/public/trips/{token}").json()
    legacy, segmented = data["bookings"]
    assert legacy["segments"] == []
    assert [s["origin"] for s in segmented["segments"]] == ["HND", "DOH"]
    assert segmented["segments"][0]["departure_dt"] == "2026-02-20T22:00:00"
    assert segmented["segments"][1]["arrival_dt"] == "2026-02-21T13:45:00"


def test_scopes_hide_whole_sections(anon, client, loaded_trip):
    token = share(client, loaded_trip["trip"]["id"], scopes=["itinerary"])["token"]
    data = anon.get(f"/api/v1/public/trips/{token}").json()
    assert data["itinerary"] and not data["bookings"] and not data["places"]

    share(client, loaded_trip["trip"]["id"], scopes=[])
    data = anon.get(f"/api/v1/public/trips/{token}").json()
    assert not data["itinerary"] and not data["bookings"] and not data["places"]
    # el viaje en sí sigue visible: el enlace es "esto es lo que vamos a hacer"
    assert data["name"] == "Japón 2026"


def test_unknown_scope_is_rejected(client, trip):
    resp = client.put(f"/api/v1/trips/{trip['id']}/share", json={"scopes": ["expenses"]})
    assert resp.status_code == 400
    assert "expenses" in resp.json()["detail"]


def test_updating_scopes_keeps_the_same_link(client, trip):
    first = share(client, trip["id"])["token"]
    assert share(client, trip["id"], scopes=["map"])["token"] == first


def test_rotate_invalidates_the_old_link(anon, client, trip):
    old = share(client, trip["id"])["token"]
    new = client.post(f"/api/v1/trips/{trip['id']}/share/rotate").json()["token"]
    assert new != old
    assert anon.get(f"/api/v1/public/trips/{old}").status_code == 404
    assert anon.get(f"/api/v1/public/trips/{new}").status_code == 200


def test_rotate_without_sharing_is_404(client, trip):
    assert client.post(f"/api/v1/trips/{trip['id']}/share/rotate").status_code == 404


def test_stop_sharing_kills_the_link(anon, client, trip):
    token = share(client, trip["id"])["token"]
    state = client.delete(f"/api/v1/trips/{trip['id']}/share").json()
    assert state == {"token": None, "scopes": []}
    assert anon.get(f"/api/v1/public/trips/{token}").status_code == 404


def test_unknown_token_is_404(anon, client, trip):
    share(client, trip["id"])
    assert anon.get("/api/v1/public/trips/no-existe").status_code == 404


def test_only_members_can_share(app, client, trip):
    make_user(client, "ajena", traveler_name="Ajena")
    other = login(app, "ajena")
    assert other.put(f"/api/v1/trips/{trip['id']}/share", json={}).status_code == 403


def test_public_cover_needs_a_valid_token(anon, client, trip):
    token = share(client, trip["id"])["token"]
    # sin portada subida, 404 (pero con token válido: no es un 404 de token)
    assert anon.get(f"/api/v1/public/trips/{token}/cover").status_code == 404
    assert anon.get("/api/v1/public/trips/otro/cover").status_code == 404
