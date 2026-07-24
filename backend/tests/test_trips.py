from datetime import date, timedelta

from conftest import add_traveler


def test_trip_crud(client):
    resp = client.post("/api/v1/trips", json={"name": "Islandia", "countries": ["IS"]})
    assert resp.status_code == 201
    trip = resp.json()
    assert trip["status"] == "planning"
    assert trip["base_currency"] == "EUR"
    assert trip["countries"] == ["IS"]
    assert trip["cover_url"] is None

    resp = client.patch(f"/api/v1/trips/{trip['id']}", json={"budget_amount": "1500.50"})
    assert resp.status_code == 200
    assert resp.json()["budget_amount"] == 1500.5

    # enlace a álbum de fotos externo
    resp = client.patch(
        f"/api/v1/trips/{trip['id']}", json={"album_url": "https://photos.app.goo.gl/abc123"}
    )
    assert resp.json()["album_url"] == "https://photos.app.goo.gl/abc123"
    resp = client.patch(f"/api/v1/trips/{trip['id']}", json={"album_url": None})
    assert resp.json()["album_url"] is None

    # varios países en un mismo viaje
    resp = client.patch(f"/api/v1/trips/{trip['id']}", json={"countries": ["is", "NO"]})
    assert resp.json()["countries"] == ["IS", "NO"]

    assert client.post("/api/v1/trips", json={"name": "X", "countries": ["XXX"]}).status_code == 422

    assert client.delete(f"/api/v1/trips/{trip['id']}").status_code == 204
    assert client.get(f"/api/v1/trips/{trip['id']}").status_code == 404


def test_trip_status_derivation(client):
    today = date.today()
    past = {
        "name": "Pasado",
        "start_date": (today - timedelta(days=10)).isoformat(),
        "end_date": (today - timedelta(days=5)).isoformat(),
    }
    resp = client.post("/api/v1/trips", json=past)
    assert resp.json()["status"] == "done"

    future = {"name": "Futuro", "start_date": (today + timedelta(days=5)).isoformat()}
    resp = client.post("/api/v1/trips", json=future)
    assert resp.json()["status"] == "upcoming"

    # override manual gana a la derivación
    trip_id = resp.json()["id"]
    resp = client.patch(f"/api/v1/trips/{trip_id}", json={"status_override": "planning"})
    assert resp.json()["status"] == "planning"

    # quitar el override vuelve al estado derivado
    resp = client.patch(f"/api/v1/trips/{trip_id}", json={"status_override": None})
    assert resp.json()["status"] == "upcoming"


def test_travelers_global_and_reusable(client, trip):
    trip_id = trip["id"]
    romm = add_traveler(client, trip_id, "Romm", "#0ea5e9")
    add_traveler(client, trip_id, "Ana")

    detail = client.get(f"/api/v1/trips/{trip_id}").json()
    assert [t["name"] for t in detail["travelers"]] == ["Ana", "Romm"]

    # crear con el mismo nombre reutiliza el viajero existente
    dup = client.post("/api/v1/travelers", json={"name": "romm"}).json()
    assert dup["id"] == romm["id"]

    # reutilizable en otro viaje
    other = client.post("/api/v1/trips", json={"name": "Otro"}).json()
    client.post(f"/api/v1/trips/{other['id']}/travelers/{romm['id']}")
    assert [t["name"] for t in client.get(f"/api/v1/trips/{other['id']}").json()["travelers"]] == [
        "Romm"
    ]

    # quitarlo de un viaje no lo borra globalmente
    client.delete(f"/api/v1/trips/{trip_id}/travelers/{romm['id']}")
    names = [t["name"] for t in client.get("/api/v1/travelers").json()]
    assert "Romm" in names

    # editar color global
    resp = client.patch(f"/api/v1/travelers/{romm['id']}", json={"color": "#16a34a"})
    assert resp.json()["color"] == "#16a34a"


def test_delete_trip_cascades(client, trip):
    trip_id = trip["id"]
    client.post(f"/api/v1/trips/{trip_id}/places", json={"name": "Fushimi Inari"})
    client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        json={"day": "2026-04-01", "description": "Ramen", "amount": "12.50"},
    )
    assert client.delete(f"/api/v1/trips/{trip_id}").status_code == 204
    assert client.get(f"/api/v1/trips/{trip_id}/places").status_code == 404
