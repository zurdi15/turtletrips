import io
import zipfile

from conftest import login, make_user
from test_backup import PNG, backup_client  # noqa: F401  (fixture reutilizada)


def _upload_avatar(client, traveler_id: int):
    return client.post(
        f"/api/v1/travelers/{traveler_id}/avatar",
        files={"file": ("cara.png", io.BytesIO(PNG), "image/png")},
    )


def test_avatar_upload_serve_replace_delete(client):
    me = client.get("/api/v1/auth/me").json()
    traveler_id = me["traveler"]["id"]

    resp = _upload_avatar(client, traveler_id)
    assert resp.status_code == 200
    avatar_url = resp.json()["avatar_url"]
    assert avatar_url and f"/travelers/{traveler_id}/avatar" in avatar_url

    served = client.get(f"/api/v1/travelers/{traveler_id}/avatar")
    assert served.status_code == 200
    assert served.content == PNG

    # reemplazar borra el anterior y cambia el cache-bust
    replaced = _upload_avatar(client, traveler_id)
    assert replaced.json()["avatar_url"] != avatar_url

    # tipo no imagen → 415
    bad = client.post(
        f"/api/v1/travelers/{traveler_id}/avatar",
        files={"file": ("doc.pdf", io.BytesIO(b"%PDF"), "application/pdf")},
    )
    assert bad.status_code == 415

    deleted = client.delete(f"/api/v1/travelers/{traveler_id}/avatar")
    assert deleted.json()["avatar_url"] is None
    assert client.get(f"/api/v1/travelers/{traveler_id}/avatar").status_code == 404


def test_avatar_permissions(app, client):
    make_user(client, "ana", traveler_name="Ana")
    make_user(client, "bob", traveler_name="Bob")
    ana, bob = login(app, "ana"), login(app, "bob")
    ana_traveler = ana.get("/api/v1/auth/me").json()["traveler"]

    # el viajero de otra cuenta no es editable; el propio y los virtuales sí
    assert _upload_avatar(bob, ana_traveler["id"]).status_code == 403
    assert _upload_avatar(ana, ana_traveler["id"]).status_code == 200
    virtual = bob.post("/api/v1/travelers", json={"name": "Peque"}).json()
    assert _upload_avatar(ana, virtual["id"]).status_code == 200


def test_avatar_survives_backup_roundtrip(backup_client):  # noqa: F811
    client, _data_dir = backup_client
    traveler_id = client.get("/api/v1/auth/me").json()["traveler"]["id"]
    assert _upload_avatar(client, traveler_id).status_code == 200

    export = client.get("/api/v1/backup/export")
    with zipfile.ZipFile(io.BytesIO(export.content)) as zf:
        avatar_entries = [n for n in zf.namelist() if n.startswith("uploads/avatars/")]
        assert len(avatar_entries) == 1

    # quitar el avatar y restaurar la copia lo recupera (fichero incluido)
    client.delete(f"/api/v1/travelers/{traveler_id}/avatar")
    resp = client.post(
        "/api/v1/backup/restore",
        files={"file": ("backup.zip", io.BytesIO(export.content), "application/zip")},
    )
    assert resp.status_code == 200, resp.text
    served = client.get(f"/api/v1/travelers/{traveler_id}/avatar")
    assert served.status_code == 200
    assert served.content == PNG
