import io

# imagen PNG mínima válida (1x1) para las subidas de postal
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d4944415478da6360000002000154a24f9f0000000049454e44ae426082"
)

DAY = "2026-06-03"


def test_journal_upsert_text_and_list(client, trip):
    tid = trip["id"]
    # sin filas al principio
    assert client.get(f"/api/v1/trips/{tid}/journal").json() == []

    # PUT crea la fila del día
    resp = client.put(
        f"/api/v1/trips/{tid}/journal/{DAY}", json={"text": "Llegada a Tokio"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["day"] == DAY
    assert body["text"] == "Llegada a Tokio"
    assert body["photo_url"] is None

    # aparece en el listado
    entries = client.get(f"/api/v1/trips/{tid}/journal").json()
    assert len(entries) == 1
    assert entries[0]["text"] == "Llegada a Tokio"

    # segundo PUT actualiza la MISMA fila (unicidad por trip+day, sin duplicar)
    resp = client.put(f"/api/v1/trips/{tid}/journal/{DAY}", json={"text": "Editado"})
    assert resp.status_code == 200
    entries = client.get(f"/api/v1/trips/{tid}/journal").json()
    assert len(entries) == 1
    assert entries[0]["text"] == "Editado"


def test_journal_photo_upload_get_delete(client, trip):
    tid = trip["id"]
    # subir postal crea la fila si no existe
    resp = client.post(
        f"/api/v1/trips/{tid}/journal/{DAY}/photo",
        files={"file": ("postal.png", io.BytesIO(PNG_1PX), "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["photo_url"] is not None
    assert f"/trips/{tid}/journal/{DAY}/photo" in body["photo_url"]

    # servir la imagen
    resp = client.get(f"/api/v1/trips/{tid}/journal/{DAY}/photo")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")

    # borrar la postal deja la fila pero sin foto
    resp = client.delete(f"/api/v1/trips/{tid}/journal/{DAY}/photo")
    assert resp.status_code == 200
    assert resp.json()["photo_url"] is None
    assert client.get(f"/api/v1/trips/{tid}/journal/{DAY}/photo").status_code == 404


def test_journal_photo_rejects_non_image(client, trip):
    tid = trip["id"]
    resp = client.post(
        f"/api/v1/trips/{tid}/journal/{DAY}/photo",
        files={"file": ("nota.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert resp.status_code == 415


def test_journal_unknown_trip_404(client):
    assert client.get("/api/v1/trips/999/journal").status_code == 404
    assert (
        client.put("/api/v1/trips/999/journal/2026-06-03", json={"text": "x"}).status_code
        == 404
    )
