"""Permisos de gestión de maletas entre miembros de una familia.

Default permitido: toda tu familia edita tus maletas hasta que TÚ revocas a
alguien (BagEditRevoke). Las maletas revocadas se siguen VIENDO (solo-consulta).
"""

from conftest import login, make_user


def _family_pair(app, client, trip):
    """Familia con ana y ben, ambos en el viaje; devuelve sus clientes."""
    family = client.post("/api/v1/families", json={"name": "García"}).json()
    ana = make_user(client, "ana", family_id=family["id"])
    ben = make_user(client, "ben", family_id=family["id"])
    for user in (ana, ben):
        resp = client.post(
            f"/api/v1/trips/{trip['id']}/travelers/{user['traveler']['id']}"
        )
        assert resp.status_code == 200, resp.text
    return ana, ben, login(app, "ana"), login(app, "ben")


def _add_item(c, trip_id: int, traveler_id: int | None, name: str):
    return c.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": name, "category": "Ropa", "traveler_id": traveler_id},
    )


def test_family_edits_by_default_until_revoked(app, client, trip):
    ana, ben, ana_c, ben_c = _family_pair(app, client, trip)
    ana_id, ben_id = ana["traveler"]["id"], ben["traveler"]["id"]

    # default: ben edita la maleta de ana
    created = _add_item(ben_c, trip["id"], ana_id, "Toalla")
    assert created.status_code == 201
    item = created.json()

    # ana revoca a ben (idempotente)
    for _ in range(2):
        resp = ana_c.put(
            f"/api/v1/family/bag-permissions/{ben_id}", json={"allowed": False}
        )
        assert resp.status_code == 204

    # ben ya no puede tocar la maleta de ana: crear, editar, borrar ni desvincular
    assert _add_item(ben_c, trip["id"], ana_id, "Gorro").status_code == 403
    assert ben_c.patch(f"/api/v1/packing/{item['id']}", json={"checked": True}).status_code == 403
    assert ben_c.delete(f"/api/v1/packing/{item['id']}").status_code == 403
    assert (
        ben_c.delete(
            f"/api/v1/trips/{trip['id']}/packing/selection?traveler_id={ana_id}"
        ).status_code
        == 403
    )

    # …pero la SIGUE VIENDO (solo-consulta), y su propia maleta y la común van bien
    visible = ben_c.get(f"/api/v1/trips/{trip['id']}/packing").json()
    assert any(i["id"] == item["id"] for i in visible)
    assert _add_item(ben_c, trip["id"], ben_id, "Libro").status_code == 201
    assert _add_item(ben_c, trip["id"], None, "Paraguas").status_code == 201

    # las listas de permisos de cada uno
    assert ana_c.get("/api/v1/family/bag-permissions").json() == {
        "revoked": [ben_id],
        "restricted_by": [],
    }
    assert ben_c.get("/api/v1/family/bag-permissions").json() == {
        "revoked": [],
        "restricted_by": [ana_id],
    }

    # ana le devuelve el permiso y ben vuelve a editar
    assert (
        ana_c.put(f"/api/v1/family/bag-permissions/{ben_id}", json={"allowed": True}).status_code
        == 204
    )
    assert _add_item(ben_c, trip["id"], ana_id, "Gorro").status_code == 201


def test_admin_bypasses_revokes(app, client, trip):
    ana, _ben, ana_c, _ben_c = _family_pair(app, client, trip)
    admin_traveler = client.get("/api/v1/auth/me").json()["traveler"]["id"]
    # ana no puede revocar al admin (otra familia) y aunque pudiera, da igual:
    resp = ana_c.put(
        f"/api/v1/family/bag-permissions/{admin_traveler}", json={"allowed": False}
    )
    assert resp.status_code == 400
    # el admin edita la maleta de ana pase lo que pase
    assert _add_item(client, trip["id"], ana["traveler"]["id"], "Linterna").status_code == 201


def test_permission_validations(app, client, trip):
    ana, _ben, ana_c, _ben_c = _family_pair(app, client, trip)
    ana_id = ana["traveler"]["id"]

    # a ti mismo no
    assert (
        ana_c.put(f"/api/v1/family/bag-permissions/{ana_id}", json={"allowed": False}).status_code
        == 400
    )
    # un viajero de otra familia (el del admin, sin familia) tampoco
    admin_traveler = client.get("/api/v1/auth/me").json()["traveler"]["id"]
    assert (
        ana_c.put(
            f"/api/v1/family/bag-permissions/{admin_traveler}", json={"allowed": False}
        ).status_code
        == 400
    )
    # inexistente → 404
    assert (
        ana_c.put("/api/v1/family/bag-permissions/99999", json={"allowed": False}).status_code
        == 404
    )


def test_virtual_bags_unaffected_by_revokes(app, client, trip):
    _ana, _ben, ana_c, ben_c = _family_pair(app, client, trip)
    # un virtual de la familia (la hereda del creador): su maleta la edita
    # todo el mundo, no hay dueño que revoque
    virtual = ana_c.post("/api/v1/travelers", json={"name": "Peque"}).json()
    assert virtual["family_id"] is not None
    client.post(f"/api/v1/trips/{trip['id']}/travelers/{virtual['id']}")
    assert _add_item(ben_c, trip["id"], virtual["id"], "Peluche").status_code == 201
    assert _add_item(ana_c, trip["id"], virtual["id"], "Cuento").status_code == 201
