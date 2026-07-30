import re
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from app.models import Family, PasswordResetToken, Traveler, UserSession
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
        # sin idioma en el payload, la cuenta nace con el default
        assert me["user"]["language"] == "en"
        assert me["user"]["theme"] == "light"
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
            json={
                "username": "zurdi",
                "password": "secret123",
                "traveler_name": "zurdi",
                "language": "es",
            },
        )
        assert resp.status_code == 201
        me = resp.json()
        # reutiliza el viajero por nombre (case-insensitive) y su familia
        assert me["traveler"]["name"] == "Zurdi"
        assert me["family"]["name"] == "Los Pérez"
        # la cuenta nace con el idioma elegido en la pantalla de login
        assert me["user"]["language"] == "es"


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


def _reset_token(caplog) -> str:
    """Token del enlace que el endpoint acaba de escribir en los logs."""
    match = re.search(r"reset-password\?token=(\S+)", caplog.text)
    assert match, caplog.text
    return match.group(1)


def test_forgot_password_logs_link_and_resets(app, client, anon, caplog):
    make_user(client, "ana")
    old = login(app, "ana")

    with caplog.at_level("INFO"):
        assert anon.post(
            "/api/v1/auth/forgot-password", json={"username": "ANA"}
        ).status_code == 204
    token = _reset_token(caplog)

    # el enlace dice para quién es antes de pedir la contraseña nueva
    info = anon.get("/api/v1/auth/reset-password", params={"token": token})
    assert info.status_code == 200
    assert info.json() == {"username": "ana"}

    resp = anon.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "nueva1234"}
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "ana"
    # queda logueado con la contraseña nueva…
    assert anon.get("/api/v1/auth/me").status_code == 200
    assert login(app, "ana", "nueva1234").get("/api/v1/auth/me").status_code == 200
    # …y las sesiones anteriores y la contraseña vieja quedan fuera
    assert old.get("/api/v1/auth/me").status_code == 401
    assert TestClient(app).post(
        "/api/v1/auth/login", json={"username": "ana", "password": "secret123"}
    ).status_code == 401

    # el enlace es de un solo uso
    assert anon.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "otra12345"}
    ).status_code == 400


def test_forgot_password_hides_unknown_user(app, client, anon, caplog, db_session):
    with caplog.at_level("INFO"):
        # misma respuesta que con un usuario real: no filtra quién tiene cuenta
        assert anon.post(
            "/api/v1/auth/forgot-password", json={"username": "nadie"}
        ).status_code == 204
    assert "reset-password?token=" not in caplog.text
    assert db_session.query(PasswordResetToken).count() == 0


def test_reset_token_expires_and_rotates(app, client, anon, caplog, db_session):
    make_user(client, "ana")

    with caplog.at_level("INFO"):
        anon.post("/api/v1/auth/forgot-password", json={"username": "ana"})
    first = _reset_token(caplog)
    caplog.clear()
    with caplog.at_level("INFO"):
        anon.post("/api/v1/auth/forgot-password", json={"username": "ana"})
    second = _reset_token(caplog)

    # pedir otro enlace invalida el anterior (solo vale el último entregado)
    assert first != second
    assert anon.get(
        "/api/v1/auth/reset-password", params={"token": first}
    ).status_code == 400

    entry = db_session.query(PasswordResetToken).one()
    entry.expires_at = datetime(2020, 1, 1)
    db_session.commit()
    assert anon.get(
        "/api/v1/auth/reset-password", params={"token": second}
    ).status_code == 400
    assert anon.post(
        "/api/v1/auth/reset-password", json={"token": second, "new_password": "nueva1234"}
    ).status_code == 400
    # el caducado se barre al tropezar con él
    assert db_session.query(PasswordResetToken).count() == 0


def test_reset_password_rejects_short_password(app, client, anon, caplog):
    make_user(client, "ana")
    with caplog.at_level("INFO"):
        anon.post("/api/v1/auth/forgot-password", json={"username": "ana"})
    token = _reset_token(caplog)
    assert anon.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "corta"}
    ).status_code == 422


def test_ics_feed_public(app, client, trip):
    token = client.post(f"/api/v1/trips/{trip['id']}/ics-token").json()["token"]
    anon = TestClient(app)
    resp = anon.get(f"/api/v1/calendar/{token}.ics")
    assert resp.status_code == 200
    assert "BEGIN:VCALENDAR" in resp.text
    assert anon.get("/api/v1/calendar/token-falso.ics").status_code == 404
