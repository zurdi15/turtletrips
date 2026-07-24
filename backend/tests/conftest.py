import os
import tempfile

# Debe fijarse antes de importar la app: get_settings() lee el entorno una sola vez
os.environ["TT_DATA_DIR"] = tempfile.mkdtemp(prefix="tt-test-")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

from app.db import Base, make_sessionmaker
from app.main import create_app


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    maker = make_sessionmaker(engine)
    session = maker()
    yield session
    session.close()


@pytest.fixture
def client(engine):
    app = create_app(engine=engine)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def trip(client):
    resp = client.post(
        "/api/v1/trips",
        json={"name": "Japón 2026", "countries": ["JP"], "base_currency": "EUR"},
    )
    assert resp.status_code == 201
    return resp.json()


def add_traveler(client, trip_id: int, name: str, color: str | None = None):
    """Crea (o reutiliza) un viajero global y lo asocia al viaje."""
    traveler = client.post("/api/v1/travelers", json={"name": name, "color": color}).json()
    resp = client.post(f"/api/v1/trips/{trip_id}/travelers/{traveler['id']}")
    assert resp.status_code == 200
    return traveler
