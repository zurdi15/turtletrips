import io

PDF_BYTES = b"%PDF-1.4 fake pdf content"


def _upload(client, trip_id, booking_id=None, content_type="application/pdf"):
    data = {}
    if booking_id is not None:
        data["booking_id"] = str(booking_id)
    return client.post(
        f"/api/v1/trips/{trip_id}/attachments",
        files={"file": ("reserva.pdf", io.BytesIO(PDF_BYTES), content_type)},
        data=data,
    )


def test_upload_download_delete(client, trip):
    trip_id = trip["id"]
    resp = _upload(client, trip_id)
    assert resp.status_code == 201
    att = resp.json()
    assert att["original_name"] == "reserva.pdf"
    assert att["size_bytes"] == len(PDF_BYTES)

    resp = client.get(f"/api/v1/attachments/{att['id']}/download")
    assert resp.status_code == 200
    assert resp.content == PDF_BYTES
    assert "attachment" in resp.headers["content-disposition"]

    resp = client.get(f"/api/v1/attachments/{att['id']}/download?inline=true")
    assert "inline" in resp.headers["content-disposition"]

    assert client.delete(f"/api/v1/attachments/{att['id']}").status_code == 204
    assert client.get(f"/api/v1/attachments/{att['id']}/download").status_code == 404


def test_upload_rejects_bad_type(client, trip):
    resp = _upload(client, trip["id"], content_type="application/x-msdownload")
    assert resp.status_code == 415


def test_upload_linked_to_booking(client, trip):
    trip_id = trip["id"]
    booking = client.post(
        f"/api/v1/trips/{trip_id}/bookings",
        json={"type": "hotel", "title": "Hotel Gracery"},
    ).json()

    resp = _upload(client, trip_id, booking_id=booking["id"])
    assert resp.status_code == 201

    listed = client.get(
        f"/api/v1/trips/{trip_id}/attachments", params={"booking_id": booking["id"]}
    ).json()
    assert len(listed) == 1

    # booking_id de otro viaje -> 400
    other = client.post("/api/v1/trips", json={"name": "Otro", "destination": "Y"}).json()
    resp = _upload(client, other["id"], booking_id=booking["id"])
    assert resp.status_code == 400
