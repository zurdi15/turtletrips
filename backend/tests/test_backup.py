import io
import json
import sqlite3
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x9a\x92\x1c1\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def backup_client(tmp_path, monkeypatch, engine):
    """Cliente con TT_DATA_DIR aislado por test (restore escribe en disco)."""
    monkeypatch.setenv("TT_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    app = create_app(engine=engine)
    with TestClient(app) as client:
        yield client, tmp_path
    get_settings.cache_clear()


def _make_trip_with_attachment(client):
    trip = client.post(
        "/api/v1/trips", json={"name": "Japón 2026", "countries": ["JP"]}
    ).json()
    attachment = client.post(
        f"/api/v1/trips/{trip['id']}/attachments",
        files={"file": ("foto.png", io.BytesIO(PNG), "image/png")},
    )
    assert attachment.status_code == 201, attachment.text
    return trip, attachment.json()


def test_export_contains_db_manifest_and_uploads(backup_client, tmp_path):
    client, data_dir = backup_client
    trip, _attachment = _make_trip_with_attachment(client)

    resp = client.get("/api/v1/backup/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "turtle-trips-backup-" in resp.headers["content-disposition"]

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = zf.namelist()
        assert "app.db" in names
        assert "manifest.json" in names
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["app"] == "turtle-trips"
        assert manifest["format"] == 1
        uploads = [n for n in names if n.startswith(f"uploads/{trip['id']}/")]
        assert len(uploads) == 1

        db_path = tmp_path / "exported.db"
        db_path.write_bytes(zf.read("app.db"))
        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT count(*) FROM trips").fetchone()[0] == 1
        conn.close()


def test_restore_roundtrip(backup_client):
    client, _data_dir = backup_client
    trip, attachment = _make_trip_with_attachment(client)

    backup_zip = client.get("/api/v1/backup/export").content
    assert client.delete(f"/api/v1/trips/{trip['id']}").status_code == 204
    assert client.get("/api/v1/trips").json() == []

    resp = client.post(
        "/api/v1/backup/restore",
        files={"file": ("backup.zip", io.BytesIO(backup_zip), "application/zip")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["restored"] is True
    assert data["trips"] == 1

    trips = client.get("/api/v1/trips").json()
    assert [t["name"] for t in trips] == ["Japón 2026"]
    download = client.get(f"/api/v1/attachments/{attachment['id']}/download")
    assert download.status_code == 200
    assert download.content == PNG


@pytest.mark.parametrize(
    "build",
    [
        lambda: b"esto no es un zip",
        lambda: _zip({"manifest.json": b"{}"}),  # sin app.db
        lambda: _zip({"app.db": b"x", "../evil": b"x"}),  # traversal
        lambda: _zip({"app.db": b"x", "otra/cosa.txt": b"x"}),  # entrada inesperada
    ],
)
def test_invalid_zip_rejected_and_data_intact(backup_client, build):
    client, _data_dir = backup_client
    _make_trip_with_attachment(client)

    resp = client.post(
        "/api/v1/backup/restore",
        files={"file": ("backup.zip", io.BytesIO(build()), "application/zip")},
    )
    assert resp.status_code == 400
    # los datos actuales siguen intactos
    assert len(client.get("/api/v1/trips").json()) == 1


def _zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_unknown_revision_rejected(backup_client, tmp_path):
    client, _data_dir = backup_client
    _make_trip_with_attachment(client)

    db_path = tmp_path / "future.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE alembic_version (version_num TEXT)")
    conn.execute("INSERT INTO alembic_version VALUES ('ffffffffffff')")
    conn.commit()
    conn.close()

    resp = client.post(
        "/api/v1/backup/restore",
        files={
            "file": (
                "backup.zip",
                io.BytesIO(_zip({"app.db": db_path.read_bytes()})),
                "application/zip",
            )
        },
    )
    assert resp.status_code == 400
    assert "versión" in resp.json()["detail"]
    assert len(client.get("/api/v1/trips").json()) == 1


def test_corrupt_db_rejected(backup_client):
    client, _data_dir = backup_client
    resp = client.post(
        "/api/v1/backup/restore",
        files={
            "file": (
                "backup.zip",
                io.BytesIO(_zip({"app.db": b"no soy sqlite"})),
                "application/zip",
            )
        },
    )
    assert resp.status_code == 400
    assert "corrupta" in resp.json()["detail"]
