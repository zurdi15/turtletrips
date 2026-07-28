"""Encuadre de las imágenes recortadas (portada, avatar y las dos postales).

Lo que se prueba aquí no es el CRUD, es la regla que se rompe en silencio:
subir una foto nueva tiene que devolver el encuadre al centro. Si no, el
recuadro que ajustaste para la foto anterior se aplica a otra distinta y la
portada sale cortada por donde no toca.
"""

import io

from conftest import add_traveler
from test_backup import PNG


def _upload_cover(client, trip_id: int):
    return client.post(
        f"/api/v1/trips/{trip_id}/cover",
        files={"file": ("portada.png", io.BytesIO(PNG), "image/png")},
    )


def test_trip_cover_focus_defaults_and_reset(client):
    trip = client.post("/api/v1/trips", json={"name": "Encuadre"}).json()
    # sin tocar nada, centrada: es lo que hacía el navegador antes de esto
    assert trip["cover_focus_x"] == 0.5
    assert trip["cover_focus_y"] == 0.5

    assert _upload_cover(client, trip["id"]).status_code == 200
    moved = client.patch(
        f"/api/v1/trips/{trip['id']}", json={"cover_focus_x": 0.2, "cover_focus_y": 0.85}
    ).json()
    assert (moved["cover_focus_x"], moved["cover_focus_y"]) == (0.2, 0.85)
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["cover_focus_x"] == 0.2

    # portada nueva → el encuadre de la anterior no se hereda
    fresh = _upload_cover(client, trip["id"]).json()
    assert (fresh["cover_focus_x"], fresh["cover_focus_y"]) == (0.5, 0.5)


def test_focus_stays_inside_the_image(client):
    trip = client.post("/api/v1/trips", json={"name": "Límites"}).json()
    for bad in ({"cover_focus_x": 1.4}, {"cover_focus_y": -0.1}):
        assert client.patch(f"/api/v1/trips/{trip['id']}", json=bad).status_code == 422
    # los extremos SÍ valen: encuadrar por el borde es legítimo
    edge = client.patch(
        f"/api/v1/trips/{trip['id']}", json={"cover_focus_x": 0, "cover_focus_y": 1}
    ).json()
    assert (edge["cover_focus_x"], edge["cover_focus_y"]) == (0.0, 1.0)


def test_avatar_focus_reset_on_upload(client):
    trip = client.post("/api/v1/trips", json={"name": "Con viajera"}).json()
    traveler = add_traveler(client, trip["id"], "Encuadrada")
    assert traveler["avatar_focus_y"] == 0.5
    client.post(
        f"/api/v1/travelers/{traveler['id']}/avatar",
        files={"file": ("cara.png", io.BytesIO(PNG), "image/png")},
    )
    moved = client.patch(
        f"/api/v1/travelers/{traveler['id']}", json={"avatar_focus_y": 0.15}
    ).json()
    assert moved["avatar_focus_y"] == 0.15
    again = client.post(
        f"/api/v1/travelers/{traveler['id']}/avatar",
        files={"file": ("otra.png", io.BytesIO(PNG), "image/png")},
    ).json()
    assert again["avatar_focus_y"] == 0.5


def test_world_photo_focus_reset_on_upload(client):
    place = client.post(
        "/api/v1/world-places", json={"name": "Kioto", "kind": "city", "country_code": "JP"}
    ).json()
    assert place["photo_focus_x"] == 0.5
    client.post(
        f"/api/v1/world-places/{place['id']}/photo",
        files={"file": ("postal.png", io.BytesIO(PNG), "image/png")},
    )
    moved = client.patch(
        f"/api/v1/world-places/{place['id']}", json={"photo_focus_x": 0.75}
    ).json()
    assert moved["photo_focus_x"] == 0.75
    again = client.post(
        f"/api/v1/world-places/{place['id']}/photo",
        files={"file": ("otra.png", io.BytesIO(PNG), "image/png")},
    ).json()
    assert again["photo_focus_x"] == 0.5


def test_journal_photo_focus_reset_on_upload(client):
    trip = client.post(
        "/api/v1/trips", json={"name": "Diario", "start_date": "2026-05-01", "end_date": "2026-05-03"}
    ).json()
    day = "2026-05-02"
    client.post(
        f"/api/v1/trips/{trip['id']}/journal/{day}/photo",
        files={"file": ("postal.png", io.BytesIO(PNG), "image/png")},
    )
    moved = client.put(
        f"/api/v1/trips/{trip['id']}/journal/{day}",
        json={"text": "Día grande", "photo_focus_y": 0.3},
    ).json()
    assert moved["photo_focus_y"] == 0.3
    again = client.post(
        f"/api/v1/trips/{trip['id']}/journal/{day}/photo",
        files={"file": ("otra.png", io.BytesIO(PNG), "image/png")},
    ).json()
    assert again["photo_focus_y"] == 0.5
    # el texto no se toca al reencuadrar ni al cambiar la foto
    assert again["text"] == "Día grande"


def test_public_trip_carries_the_cover_focus(client):
    trip = client.post("/api/v1/trips", json={"name": "Compartido"}).json()
    _upload_cover(client, trip["id"])
    client.patch(f"/api/v1/trips/{trip['id']}", json={"cover_focus_y": 0.1})
    token = client.put(f"/api/v1/trips/{trip['id']}/share", json={"scopes": ["map"]}).json()["token"]

    public = client.get(f"/api/v1/public/trips/{token}").json()
    assert public["cover_focus_y"] == 0.1
