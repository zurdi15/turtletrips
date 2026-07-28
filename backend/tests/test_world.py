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
    # la fecha de visita se hereda del final del viaje
    assert by_name["VN"]["visited_year"] == 2024
    assert by_name["VN"]["visited_month"] == 2
    assert by_name["Hanói"]["visited_year"] == 2024
    # sitio visitado (ciudad) y sitio con gasto, agrupables por país
    assert by_name["Hanói"]["kind"] == "city"
    assert by_name["Hanói"]["country_code"] == "VN"
    assert by_name["Bahía de Halong"]["kind"] == "place"
    # el no visitado y sin gasto no entra
    assert "Sapa" not in by_name

    # el sync es idempotente
    assert len(client.get("/api/v1/world-places").json()) == len(world)

    # editar la nota de una entrada auto sí se conserva
    resp = client.patch(
        f"/api/v1/world-places/{by_name['Hanói']['id']}", json={"note": "Pho increíble"}
    )
    assert resp.json()["note"] == "Pho increíble"
    assert visited["id"] is not None

    # un país con ciudades/sitios visibles no se puede borrar
    assert client.delete(f"/api/v1/world-places/{by_name['VN']['id']}").status_code == 409
    # sin ellos sí: borrar una entrada auto la oculta y NO reaparece
    for name in ("Hanói", "Bahía de Halong"):
        assert client.delete(f"/api/v1/world-places/{by_name[name]['id']}").status_code == 204
    assert client.delete(f"/api/v1/world-places/{by_name['VN']['id']}").status_code == 204
    names = [w["name"] for w in client.get("/api/v1/world-places").json()]
    assert "VN" not in names
    assert "Hanói" not in names


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

    # con la ciudad viva el país no se puede borrar
    assert client.delete(f"/api/v1/world-places/{country['id']}").status_code == 409

    # sin ciudades sí (auto → hidden); añadir otra ciudad NO debe revivirlo
    assert client.delete(f"/api/v1/world-places/{city['id']}").status_code == 204
    assert client.delete(f"/api/v1/world-places/{country['id']}").status_code == 204
    client.post(
        "/api/v1/world-places",
        json={"name": "Oporto", "kind": "city", "country_code": "PT"},
    )
    listed = client.get("/api/v1/world-places").json()
    assert not any(p["kind"] == "country" for p in listed)


def test_country_inherits_earliest_city_date(client):
    # ciudad con fecha: arrastra el país, que hereda esa fecha
    client.post(
        "/api/v1/world-places",
        json={
            "name": "Kioto", "kind": "city", "country_code": "JP",
            "visited_year": 2019, "visited_month": 4,
        },
    )
    listed = {p["name"]: p for p in client.get("/api/v1/world-places").json()}
    assert listed["JP"]["visited_year"] == 2019
    assert listed["JP"]["visited_month"] == 4

    # una ciudad ANTERIOR manda: el país pasa a la visita más antigua
    client.post(
        "/api/v1/world-places",
        json={
            "name": "Tokio", "kind": "city", "country_code": "JP",
            "visited_year": 2015, "visited_month": 11,
        },
    )
    listed = {p["name"]: p for p in client.get("/api/v1/world-places").json()}
    assert (listed["JP"]["visited_year"], listed["JP"]["visited_month"]) == (2015, 11)

    # el año a secas es menos preciso: gana como "lo más antiguo conocido"
    client.post(
        "/api/v1/world-places",
        json={"name": "Osaka", "kind": "city", "country_code": "JP", "visited_year": 2015},
    )
    listed = {p["name"]: p for p in client.get("/api/v1/world-places").json()}
    assert (listed["JP"]["visited_year"], listed["JP"]["visited_month"]) == (2015, None)

    # la fecha PROPIA del país manda sobre la heredada
    client.patch(
        f"/api/v1/world-places/{listed['JP']['id']}",
        json={"visited_year": 2012, "visited_month": 1},
    )
    listed = {p["name"]: p for p in client.get("/api/v1/world-places").json()}
    assert (listed["JP"]["visited_year"], listed["JP"]["visited_month"]) == (2012, 1)


def test_stats_use_inherited_country_date(client):
    client.post(
        "/api/v1/world-places",
        json={"name": "Hanói", "kind": "city", "country_code": "VN", "visited_year": 2017},
    )
    years = {y["year"]: y for y in client.get("/api/v1/stats/yearly").json()}
    # el país sin fecha propia cuenta en el año de su ciudad más antigua
    assert years[2017]["countries"] == ["VN"]


def test_world_photo_upload_and_delete(client):
    import io

    country = client.post(
        "/api/v1/world-places",
        json={"name": "Japón", "kind": "country", "country_code": "JP"},
    ).json()

    resp = client.post(
        f"/api/v1/world-places/{country['id']}/photo",
        files={"file": ("fuji.jpg", io.BytesIO(b"fake image bytes"), "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["photo_url"] is not None

    photo = client.get(f"/api/v1/world-places/{country['id']}/photo")
    assert photo.status_code == 200
    assert photo.content == b"fake image bytes"

    # solo imágenes
    resp = client.post(
        f"/api/v1/world-places/{country['id']}/photo",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
    )
    assert resp.status_code == 415

    resp = client.delete(f"/api/v1/world-places/{country['id']}/photo")
    assert resp.json()["photo_url"] is None
    assert client.get(f"/api/v1/world-places/{country['id']}/photo").status_code == 404


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


def test_world_regions(client):
    """Regiones (ISO 3166-2): arrastran su país y alimentan su fecha derivada."""
    region = client.post(
        "/api/v1/world-places",
        json={
            "name": "Cataluña", "kind": "region",
            "country_code": "es", "region_code": "es-ct", "visited_year": 2019,
        },
    )
    assert region.status_code == 201
    assert region.json()["region_code"] == "ES-CT"

    listed = client.get("/api/v1/world-places").json()
    by_kind = {p["kind"]: p for p in listed}
    # marcar una región mete su país en el diario…
    assert set(by_kind) == {"region", "country"}
    # …y el país hereda el año de la región (no tiene fecha propia)
    assert by_kind["country"]["country_code"] == "ES"
    assert by_kind["country"]["visited_year"] == 2019

    # el país ya no se puede quitar mientras cuelgue la región
    country_id = by_kind["country"]["id"]
    conflict = client.delete(f"/api/v1/world-places/{country_id}")
    assert conflict.status_code == 409
    assert "regiones" in conflict.json()["detail"]

    assert client.delete(f"/api/v1/world-places/{region.json()['id']}").status_code == 204
    assert client.delete(f"/api/v1/world-places/{country_id}").status_code == 204


def test_world_region_requires_matching_country(client):
    # sin código de región
    missing = client.post(
        "/api/v1/world-places",
        json={"name": "Cataluña", "kind": "region", "country_code": "ES"},
    )
    assert missing.status_code == 400

    # la región no pertenece a ese país
    mismatch = client.post(
        "/api/v1/world-places",
        json={
            "name": "Cataluña", "kind": "region",
            "country_code": "FR", "region_code": "ES-CT",
        },
    )
    assert mismatch.status_code == 400
    assert "no pertenece" in mismatch.json()["detail"]


def test_world_region_patch_keeps_codes(client):
    """Editar la nota de una región no debe exigir repetir sus códigos."""
    region = client.post(
        "/api/v1/world-places",
        json={
            "name": "Hokkaido", "kind": "region",
            "country_code": "JP", "region_code": "JP-01",
        },
    ).json()
    resp = client.patch(
        f"/api/v1/world-places/{region['id']}", json={"note": "Volver en invierno"}
    )
    assert resp.status_code == 200
    assert resp.json()["region_code"] == "JP-01"
