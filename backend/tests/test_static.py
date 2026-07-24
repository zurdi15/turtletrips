import pytest

from app.main import STATIC_DIR


@pytest.mark.skipif(
    not (STATIC_DIR / "sw.js").is_file(), reason="no hay build del frontend en static/"
)
def test_service_worker_and_manifest_not_cached(client):
    resp = client.get("/sw.js")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-cache"

    resp = client.get("/manifest.webmanifest")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-cache"
    assert resp.headers["content-type"].startswith("application/manifest+json")


@pytest.mark.skipif(
    not (STATIC_DIR / "index.html").is_file(), reason="no hay build del frontend en static/"
)
def test_spa_index_not_cached(client):
    resp = client.get("/cualquier/ruta-spa")
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "no-cache"
