"""Documentos personales de la familia: DNI, pasaporte, carnet…

Cuelgan de la familia (los ve toda), nunca de un viaje, y no salen por el
enlace público.
"""

import io

from conftest import add_traveler, login, make_user

PDF_BYTES = b"%PDF-1.4 pasaporte"


def _upload(client, traveler_id, name="pasaporte.pdf", content_type="application/pdf"):
    return client.post(
        "/api/v1/documents",
        files={"file": (name, io.BytesIO(PDF_BYTES), content_type)},
        data={"traveler_id": str(traveler_id)},
    )


def _family_with_two(app, client, trip):
    family = client.post("/api/v1/families", json={"name": "García"}).json()
    ana = make_user(client, "ana", family_id=family["id"])
    ben = make_user(client, "ben", family_id=family["id"])
    return family, ana, ben, login(app, "ana"), login(app, "ben")


def test_upload_list_download_and_delete(app, client, trip):
    family, ana, _ben, ana_c, ben_c = _family_with_two(app, client, trip)

    resp = _upload(ana_c, ana["traveler"]["id"])
    assert resp.status_code == 201, resp.text
    doc = resp.json()
    assert doc["original_name"] == "pasaporte.pdf"
    assert doc["traveler_id"] == ana["traveler"]["id"]

    # lo ve toda la familia, no solo quien lo subió
    assert [d["id"] for d in ben_c.get("/api/v1/documents").json()] == [doc["id"]]
    resp = ben_c.get(f"/api/v1/documents/{doc['id']}/download")
    assert resp.status_code == 200
    assert resp.content == PDF_BYTES

    # renombrar conserva la extensión, como en los ficheros del viaje
    resp = ben_c.patch(f"/api/v1/documents/{doc['id']}", json={"original_name": "Pasaporte Ana"})
    assert resp.json()["original_name"] == "Pasaporte Ana.pdf"

    assert ben_c.delete(f"/api/v1/documents/{doc['id']}").status_code == 204
    assert ana_c.get("/api/v1/documents").json() == []


def test_documents_of_a_virtual_traveler(app, client, trip):
    family, ana, _ben, ana_c, _ben_c = _family_with_two(app, client, trip)
    kid = client.post(
        "/api/v1/travelers", json={"name": "Crío", "family_id": family["id"]}
    ).json()

    resp = _upload(ana_c, kid["id"], name="pasaporte-crio.pdf")
    assert resp.status_code == 201
    assert resp.json()["traveler_id"] == kid["id"]


def test_other_families_never_see_them(app, client, trip):
    _family, ana, _ben, ana_c, _ben_c = _family_with_two(app, client, trip)
    doc = _upload(ana_c, ana["traveler"]["id"]).json()

    otra = client.post("/api/v1/families", json={"name": "Otra"}).json()
    make_user(client, "ajena", family_id=otra["id"])
    ajena_c = login(app, "ajena")

    assert ajena_c.get("/api/v1/documents").json() == []
    assert ajena_c.get(f"/api/v1/documents/{doc['id']}/download").status_code == 403
    assert ajena_c.patch(f"/api/v1/documents/{doc['id']}", json={"original_name": "x"}).status_code == 403
    assert ajena_c.delete(f"/api/v1/documents/{doc['id']}").status_code == 403

    # ni subir un documento a nombre de alguien de otra familia
    assert _upload(ajena_c, ana["traveler"]["id"]).status_code == 403


def test_rejects_unsupported_files(app, client, trip):
    _family, ana, _ben, ana_c, _ben_c = _family_with_two(app, client, trip)
    resp = _upload(ana_c, ana["traveler"]["id"], name="virus.exe", content_type="application/x-msdownload")
    assert resp.status_code == 415


def test_documents_need_a_family(app, client, trip):
    """Sin familia no hay dónde guardarlos: 403 accionable, no una lista vacía."""
    make_user(client, "suelto")  # sin family_id
    suelto = login(app, "suelto")
    assert suelto.get("/api/v1/documents").status_code == 403
    assert _upload(suelto, 1).status_code == 403
