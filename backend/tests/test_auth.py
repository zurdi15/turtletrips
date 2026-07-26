from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.models import Family, Traveler, UserSession
from conftest import ADMIN, bootstrap, login, make_user


def test_status_and_bootstrap_flow(app):
    with TestClient(app) as c:
        assert c.get("/api/v1/auth/status").json() == {"bootstrapped": False}
        # sin sesión, la API está cerrada pero health y auth son públicos
        assert c.get("/api/v1/trips").status_code == 401
        assert c.get("/api/v1/health").status_code == 200

        me = bootstrap(c)
        assert me["user"]["username"] == "admin"
        assert me["user"]["is_admin"] is True
        assert me["traveler"]["name"] == "Admin"
        assert me["traveler"]["has_user"] is True
        assert me["family"]["name"] == "Familia"

        assert c.get("/api/v1/auth/status").json() == {"bootstrapped": True}
        # la cookie de sesión abre la API
        assert c.get("/api/v1/trips").status_code == 200
        # segundo bootstrap rechazado
        assert c.post("/api/v1/auth/bootstrap", json=ADMIN).status_code == 409


def test_bootstrap_reuses_existing_traveler_and_family(app, db_session):
    # instancia "migrada": familia y viajero preexistentes sin usuarios
    family = Family(name="Los Pérez")
    db_session.add(family)
    db_session.flush()
    db_session.add(Traveler(name="Zurdi", family_id=family.id))
    db_session.commit()

    with TestClient(app) as c:
        resp = c.post(
            "/api/v1/auth/bootstrap",
            json={"username": "zurdi", "password": "secret123", "traveler_name": "zurdi"},
        )
        assert resp.status_code == 201
        me = resp.json()
        # reutiliza el viajero por nombre (case-insensitive) y su familia
        assert me["traveler"]["name"] == "Zurdi"
        assert me["family"]["name"] == "Los Pérez"


def test_login_logout(app, client):
    make_user(client, "ana")
    c = login(app, "ana")
    assert c.get("/api/v1/auth/me").json()["user"]["username"] == "ana"

    # credenciales malas: mismo 401 exista o no el usuario
    bad = TestClient(app)
    assert bad.post(
        "/api/v1/auth/login", json={"username": "ana", "password": "nope-nope"}
    ).status_code == 401
    assert bad.post(
        "/api/v1/auth/login", json={"username": "nadie", "password": "nope-nope"}
    ).status_code == 401

    assert c.post("/api/v1/auth/logout").status_code == 204
    assert c.get("/api/v1/auth/me").status_code == 401


def test_session_cookie_is_httponly(app):
    with TestClient(app) as c:
        resp = c.post("/api/v1/auth/bootstrap", json=ADMIN)
        cookie = resp.headers["set-cookie"]
        assert "tt_session=" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=lax" in cookie.replace("samesite", "SameSite")


def test_me_settings_persist(client):
    resp = client.patch(
        "/api/v1/auth/me/settings", json={"theme": "dark", "language": "es"}
    )
    assert resp.status_code == 200
    me = client.get("/api/v1/auth/me").json()
    assert me["user"]["theme"] == "dark"
    assert me["user"]["language"] == "es"
    # valores fuera del enum → 422
    assert client.patch("/api/v1/auth/me/settings", json={"theme": "neon"}).status_code == 422


def test_change_password_revokes_other_sessions(app, client):
    make_user(client, "ana")
    first = login(app, "ana")
    second = login(app, "ana")

    wrong = first.post(
        "/api/v1/auth/me/password",
        json={"current_password": "mala", "new_password": "nueva1234"},
    )
    assert wrong.status_code == 400

    ok = first.post(
        "/api/v1/auth/me/password",
        json={"current_password": "secret123", "new_password": "nueva1234"},
    )
    assert ok.status_code == 204
    # la sesión que cambió la contraseña sigue viva; la otra queda revocada
    assert first.get("/api/v1/auth/me").status_code == 200
    assert second.get("/api/v1/auth/me").status_code == 401
    assert login(app, "ana", "nueva1234").get("/api/v1/auth/me").status_code == 200


def test_expired_session_rejected(app, client, db_session):
    session_row = db_session.query(UserSession).first()
    session_row.expires_at = datetime(2020, 1, 1)
    db_session.commit()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_sliding_expiry_renews(app, client, db_session):
    session_row = db_session.query(UserSession).first()
    # a punto de caducar (por debajo de la mitad del TTL)
    session_row.expires_at = datetime.now() + timedelta(days=1)
    db_session.commit()
    assert client.get("/api/v1/auth/me").status_code == 200
    db_session.expire_all()
    renewed = db_session.query(UserSession).first()
    assert renewed.expires_at > datetime.now() + timedelta(days=25)


def test_ics_feed_public(app, client, trip):
    token = client.post(f"/api/v1/trips/{trip['id']}/ics-token").json()["token"]
    anon = TestClient(app)
    resp = anon.get(f"/api/v1/calendar/{token}.ics")
    assert resp.status_code == 200
    assert "BEGIN:VCALENDAR" in resp.text
    assert anon.get("/api/v1/calendar/token-falso.ics").status_code == 404
