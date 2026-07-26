from conftest import login, make_user


def _traveler_by_name(client, name: str) -> dict:
    return next(t for t in client.get("/api/v1/travelers").json() if t["name"] == name)


def test_create_user_with_new_traveler(client):
    user = make_user(client, "ana", traveler_name="Ana")
    assert user["username"] == "ana"
    assert user["traveler"]["name"] == "Ana"
    traveler = _traveler_by_name(client, "Ana")
    assert traveler["has_user"] is True


def test_create_user_linking_virtual_traveler(client):
    # viajero virtual pre-existente (p. ej. creado antes de darle cuenta)
    virtual = client.post("/api/v1/travelers", json={"name": "Bob"}).json()
    assert virtual["has_user"] is False
    user = make_user(client, "bob", traveler_id=virtual["id"])
    assert user["traveler"]["id"] == virtual["id"]
    # el mismo viajero no puede tener dos cuentas
    resp = client.post(
        "/api/v1/users",
        json={"username": "bob2", "password": "secret123", "traveler_id": virtual["id"]},
    )
    assert resp.status_code == 409


def test_duplicate_username_rejected(client):
    make_user(client, "ana")
    resp = client.post(
        "/api/v1/users",
        json={"username": "Ana", "password": "secret123", "traveler_name": "Otra"},
    )
    assert resp.status_code == 409


def test_user_endpoints_are_admin_only(app, client):
    make_user(client, "ana")
    ana = login(app, "ana")
    assert ana.get("/api/v1/users").status_code == 403
    assert ana.post(
        "/api/v1/users",
        json={"username": "x", "password": "secret123", "traveler_name": "X"},
    ).status_code == 403
    assert ana.get("/api/v1/backup/export").status_code == 403


def test_delete_user_keeps_traveler_as_virtual(app, client):
    user = make_user(client, "ana", traveler_name="Ana")
    ana = login(app, "ana")
    assert client.delete(f"/api/v1/users/{user['id']}").status_code == 204
    # su sesión cae con la cuenta (CASCADE) y el viajero queda virtual
    assert ana.get("/api/v1/auth/me").status_code == 401
    assert _traveler_by_name(client, "Ana")["has_user"] is False


def test_last_admin_protected(client):
    me = client.get("/api/v1/auth/me").json()
    admin_id = me["user"]["id"]
    assert client.delete(f"/api/v1/users/{admin_id}").status_code == 409
    assert client.patch(
        f"/api/v1/users/{admin_id}", json={"is_admin": False}
    ).status_code == 409
    # con un segundo admin ya se puede degradar al primero
    make_user(client, "root2", is_admin=True)
    assert client.patch(
        f"/api/v1/users/{admin_id}", json={"is_admin": False}
    ).status_code == 200


def test_reset_password_revokes_sessions(app, client):
    user = make_user(client, "ana")
    ana = login(app, "ana")
    resp = client.post(
        f"/api/v1/users/{user['id']}/password", json={"new_password": "reseteada1"}
    )
    assert resp.status_code == 204
    assert ana.get("/api/v1/auth/me").status_code == 401
    assert login(app, "ana", "reseteada1").get("/api/v1/auth/me").status_code == 200


def test_families_crud_and_guards(app, client):
    # crear siembra las categorías por defecto de la familia
    family = client.post("/api/v1/families", json={"name": "Los García"}).json()
    make_user(client, "ana", family_id=family["id"])
    ana = login(app, "ana")
    cats = ana.get("/api/v1/categories?kind=expense").json()
    assert len(cats) == 9

    # GET es para cualquier usuario; mutaciones solo admin
    assert ana.get("/api/v1/families").status_code == 200
    assert ana.post("/api/v1/families", json={"name": "Hackers"}).status_code == 403
    assert ana.patch(
        f"/api/v1/families/{family['id']}", json={"name": "Hackers"}
    ).status_code == 403

    # renombrar y duplicados
    assert client.post("/api/v1/families", json={"name": "los garcía"}).status_code == 409
    renamed = client.patch(f"/api/v1/families/{family['id']}", json={"name": "García"})
    assert renamed.json()["name"] == "García"

    # borrar con viajeros → 409; vacía → ok
    assert client.delete(f"/api/v1/families/{family['id']}").status_code == 409
    empty = client.post("/api/v1/families", json={"name": "Vacía"}).json()
    assert client.delete(f"/api/v1/families/{empty['id']}").status_code == 204


def test_admin_assigns_traveler_family(app, client):
    family = client.post("/api/v1/families", json={"name": "B"}).json()
    make_user(client, "ana")
    ana = login(app, "ana")
    virtual = client.post("/api/v1/travelers", json={"name": "Peque"}).json()
    # el admin puede mover viajeros de familia; un usuario normal no
    assert ana.patch(
        f"/api/v1/travelers/{virtual['id']}", json={"family_id": family["id"]}
    ).status_code == 403
    moved = client.patch(
        f"/api/v1/travelers/{virtual['id']}", json={"family_id": family["id"]}
    )
    assert moved.status_code == 200
    assert moved.json()["family_id"] == family["id"]
