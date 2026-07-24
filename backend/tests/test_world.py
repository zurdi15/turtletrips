def test_world_places_crud(client):
    country = client.post(
        "/api/v1/world-places",
        json={"name": "Japón", "kind": "country", "country_code": "jp"},
    )
    assert country.status_code == 201
    assert country.json()["country_code"] == "JP"

    city = client.post(
        "/api/v1/world-places",
        json={
            "name": "Taipéi", "kind": "city", "country_code": "TW",
            "lat": 25.03, "lon": 121.56, "note": "La capital, 3 días",
        },
    ).json()

    listed = client.get("/api/v1/world-places").json()
    assert [p["name"] for p in listed] == ["Japón", "Taipéi"]

    resp = client.patch(
        f"/api/v1/world-places/{city['id']}", json={"note": "Volver al mercado nocturno"}
    )
    assert resp.json()["note"] == "Volver al mercado nocturno"

    assert client.post("/api/v1/world-places", json={"name": "X", "kind": "galaxy"}).status_code == 422

    assert client.delete(f"/api/v1/world-places/{city['id']}").status_code == 204
    assert len(client.get("/api/v1/world-places").json()) == 1


def test_world_auto_sync_from_trips(client):
    # viaje TERMINADO (fechas pasadas) con países
    trip = client.post(
        "/api/v1/trips",
        json={
            "name": "Vietnam 2024", "countries": ["VN"],
            "start_date": "2024-02-01", "end_date": "2024-02-15",
        },
    ).json()
    # sitio visitado, sitio con gasto y sitio pendiente (no debe entrar)
    visited = client.post(
        f"/api/v1/trips/{trip['id']}/places",
        json={"name": "Hanói", "category": "city", "visited": True, "lat": 21.0, "lon": 105.8},
    ).json()
    with_expense = client.post(
        f"/api/v1/trips/{trip['id']}/places",
        json={"name": "Bahía de Halong", "category": "nature"},
    ).json()
    client.post(
        f"/api/v1/trips/{trip['id']}/places", json={"name": "Sapa", "category": "town"}
    )
    client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2024-02-05", "description": "Crucero", "amount": "120",
            "place_id": with_expense["id"],
        },
    )

    world = client.get("/api/v1/world-places").json()
    by_name = {w["name"]: w for w in world}
    # país del viaje terminado, con origen
    assert by_name["VN"]["kind"] == "country"
    assert by_name["VN"]["auto"] is True
    assert by_name["VN"]["origin"] == "Vietnam 2024"
    # sitio visitado (ciudad) y sitio con gasto, agrupables por país
    assert by_name["Hanói"]["kind"] == "city"
    assert by_name["Hanói"]["country_code"] == "VN"
    assert by_name["Bahía de Halong"]["kind"] == "place"
    # el no visitado y sin gasto no entra
    assert "Sapa" not in by_name

    # el sync es idempotente
    assert len(client.get("/api/v1/world-places").json()) == len(world)

    # borrar una entrada auto la oculta y NO reaparece
    client.delete(f"/api/v1/world-places/{by_name['VN']['id']}")
    names = [w["name"] for w in client.get("/api/v1/world-places").json()]
    assert "VN" not in names

    # editar la nota de una entrada auto sí se conserva
    resp = client.patch(
        f"/api/v1/world-places/{by_name['Hanói']['id']}", json={"note": "Pho increíble"}
    )
    assert resp.json()["note"] == "Pho increíble"
    assert visited["id"] is not None


def test_world_upcoming_trip_does_not_add_country(client):
    client.post(
        "/api/v1/trips",
        json={
            "name": "Futuro", "countries": ["IS"],
            "start_date": "2030-01-01", "end_date": "2030-01-10",
        },
    )
    names = [w["name"] for w in client.get("/api/v1/world-places").json()]
    assert "IS" not in names
