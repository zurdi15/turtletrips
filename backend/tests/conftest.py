import os
import tempfile

# Debe fijarse antes de importar la app: get_settings() lee el entorno una sola vez
os.environ["TT_DATA_DIR"] = tempfile.mkdtemp(prefix="tt-test-")
# coste mínimo de bcrypt: cada test hace bootstrap/login y el coste real (~0,3 s) sumaría minutos
os.environ["TT_BCRYPT_ROUNDS"] = "4"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

from app.db import Base, make_sessionmaker
from app.main import create_app

# credenciales del admin que crea el fixture `client` vía bootstrap
ADMIN = {"username": "admin", "password": "admin1234", "traveler_name": "Admin"}


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
def app(engine):
    return create_app(engine=engine)


def bootstrap(client: TestClient) -> dict:
    """Crea la cuenta admin inicial; la cookie de sesión queda en el client."""
    resp = client.post("/api/v1/auth/bootstrap", json=ADMIN)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def client(app):
    """Cliente logueado como admin (bypass de membresía: la suite histórica
    opera sobre cualquier viaje sin figurar como viajero)."""
    with TestClient(app) as client:
        bootstrap(client)
        yield client


@pytest.fixture
def anon(app):
    """Cliente sin sesión (la instancia ya está bootstrapeada por `client`)."""
    with TestClient(app) as client:
        yield client


def make_user(
    admin_client: TestClient,
    username: str,
    *,
    password: str = "secret123",
    traveler_name: str | None = None,
    traveler_id: int | None = None,
    family_id: int | None = None,
    is_admin: bool = False,
) -> dict:
    """Crea un usuario vía API admin (viajero nuevo por nombre o vinculando uno)."""
    payload: dict = {"username": username, "password": password, "is_admin": is_admin}
    if traveler_id is not None:
        payload["traveler_id"] = traveler_id
    else:
        payload["traveler_name"] = traveler_name or username.capitalize()
    if family_id is not None:
        payload["family_id"] = family_id
    resp = admin_client.post("/api/v1/users", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def login(app, username: str, password: str = "secret123") -> TestClient:
    """Cliente nuevo con su propia cookie jar, logueado como `username`."""
    client = TestClient(app)
    resp = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return client


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
