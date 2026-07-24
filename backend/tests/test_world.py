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
    # la ciudad de TW arrastra su país (entrada auto con el código como nombre)
    assert sorted(p["name"] for p in listed) == ["Japón", "TW", "Taipéi"]

    resp = client.patch(
        f"/api/v1/world-places/{city['id']}", json={"note": "Volver al mercado nocturno"}
    )
    assert resp.json()["note"] == "Volver al mercado nocturno"

    assert client.post("/api/v1/world-places", json={"name": "X", "kind": "galaxy"}).status_code == 422

    assert client.delete(f"/api/v1/world-places/{city['id']}").status_code == 204
    assert len(client.get("/api/v1/world-places").json()) == 2


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


def test_city_implies_country_entry(client):
    city = client.post(
        "/api/v1/world-places",
        json={"name": "Lisboa", "kind": "city", "country_code": "PT"},
    ).json()
    assert city["country_code"] == "PT"

    listed = client.get("/api/v1/world-places").json()
    country = next(p for p in listed if p["kind"] == "country")
    assert country["country_code"] == "PT"
    assert country["auto"] is True

    # borrar el país (auto → hidden) y añadir otra ciudad: NO debe revivir
    client.delete(f"/api/v1/world-places/{country['id']}")
    client.post(
        "/api/v1/world-places",
        json={"name": "Oporto", "kind": "city", "country_code": "PT"},
    )
    listed = client.get("/api/v1/world-places").json()
    assert not any(p["kind"] == "country" for p in listed)


def test_sync_visited_place_pulls_country(client):
    # viaje EN CURSO/futuro (no terminado) con un solo país
    trip = client.post(
        "/api/v1/trips",
        json={"name": "Italia", "countries": ["IT"], "start_date": "2030-01-01"},
    ).json()
    client.post(
        f"/api/v1/trips/{trip['id']}/places",
        json={"name": "Coliseo", "visited": True},
    )

    listed = client.get("/api/v1/world-places").json()
    kinds = {p["kind"] for p in listed}
    # el sitio visitado entra por el sync y arrastra su país aunque el viaje no haya terminado
    assert kinds == {"place", "country"}
    country = next(p for p in listed if p["kind"] == "country")
    assert country["country_code"] == "IT"
    assert country["origin"] == "Italia"
