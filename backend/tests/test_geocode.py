from app.services import geocode as geocode_service


def test_reverse_geocode_endpoint(client, monkeypatch):
    calls: list[tuple[str, dict]] = []

    async def fake_nominatim(path, params):
        calls.append((path, params))
        return {"display_name": "Hotel Gracery, Shinjuku, Tokio", "lat": "35.6951", "lon": "139.7008"}

    monkeypatch.setattr(geocode_service, "_nominatim", fake_nominatim)
    monkeypatch.setattr(geocode_service, "_cache", {})

    resp = client.get("/api/v1/geocode/reverse?lat=35.69512&lon=139.70081")
    assert resp.status_code == 200
    assert resp.json() == {
        "display_name": "Hotel Gracery, Shinjuku, Tokio",
        "lat": 35.6951,
        "lon": 139.7008,
    }
    assert calls[0][0] == "reverse"

    # un segundo toque a ~10 m sale de la caché sin pasar por Nominatim
    resp = client.get("/api/v1/geocode/reverse?lat=35.69514&lon=139.70083")
    assert resp.status_code == 200
    assert len(calls) == 1


def test_reverse_geocode_nothing_there(client, monkeypatch):
    async def fake_nominatim(path, params):
        return {"error": "Unable to geocode"}

    monkeypatch.setattr(geocode_service, "_nominatim", fake_nominatim)
    monkeypatch.setattr(geocode_service, "_cache", {})

    assert client.get("/api/v1/geocode/reverse?lat=0&lon=-160").status_code == 404
    # fuera de rango: validación, no una llamada fuera
    assert client.get("/api/v1/geocode/reverse?lat=91&lon=0").status_code == 422


def test_search_still_works(client, monkeypatch):
    async def fake_nominatim(path, params):
        assert path == "search" and params["q"] == "Shinjuku"
        return [{"display_name": "Shinjuku, Tokio", "lat": "35.69", "lon": "139.70"}]

    monkeypatch.setattr(geocode_service, "_nominatim", fake_nominatim)
    monkeypatch.setattr(geocode_service, "_cache", {})

    resp = client.get("/api/v1/geocode?q=Shinjuku")
    assert resp.status_code == 200
    assert resp.json()[0]["display_name"] == "Shinjuku, Tokio"
