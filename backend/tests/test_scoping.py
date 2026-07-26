"""Aislamiento multi-usuario: membresía de viajes y scoping por familia."""

import pytest

from conftest import login, make_user


@pytest.fixture
def two_families(app, client):
    """admin (familia 'Familia') + bob (misma familia) + ana (familia 'B')."""
    family_b = client.post("/api/v1/families", json={"name": "B"}).json()
    admin_family_id = client.get("/api/v1/auth/me").json()["family"]["id"]
    make_user(client, "bob", family_id=admin_family_id)
    make_user(client, "ana", family_id=family_b["id"])
    return {
        "admin": client,
        "bob": login(app, "bob"),
        "ana": login(app, "ana"),
        "family_a": admin_family_id,
        "family_b": family_b["id"],
    }


def _me_traveler(client) -> dict:
    return client.get("/api/v1/auth/me").json()["traveler"]


def test_trip_membership_controls_access(two_families):
    bob, ana, admin = two_families["bob"], two_families["ana"], two_families["admin"]
    trip = bob.post("/api/v1/trips", json={"name": "Escapada"}).json()
    # el creador queda como viajero automáticamente
    assert [t["name"] for t in trip["travelers"]] == ["Bob"]
    assert trip["family_id"] == two_families["family_a"]

    trip_id = trip["id"]
    # ana no participa: ni detalle, ni lista, ni recursos anidados/planos
    assert ana.get(f"/api/v1/trips/{trip_id}").status_code == 403
    assert trip_id not in [t["id"] for t in ana.get("/api/v1/trips").json()]
    assert ana.get(f"/api/v1/trips/{trip_id}/expenses").status_code == 403
    assert ana.post(
        f"/api/v1/trips/{trip_id}/places", json={"name": "Sitio"}
    ).status_code == 403

    place = bob.post(f"/api/v1/trips/{trip_id}/places", json={"name": "Sitio"}).json()
    assert ana.patch(f"/api/v1/places/{place['id']}", json={"name": "X"}).status_code == 403
    assert ana.delete(f"/api/v1/places/{place['id']}").status_code == 403

    # el admin ve y edita todo (bypass)
    assert admin.get(f"/api/v1/trips/{trip_id}").status_code == 200
    assert trip_id in [t["id"] for t in admin.get("/api/v1/trips").json()]

    # al añadir a ana, entra con todos los permisos (todos editan todo)
    ana_traveler = _me_traveler(ana)
    bob.post(f"/api/v1/trips/{trip_id}/travelers/{ana_traveler['id']}")
    assert ana.get(f"/api/v1/trips/{trip_id}").status_code == 200
    assert ana.patch(
        f"/api/v1/trips/{trip_id}", json={"name": "Escapada conjunta"}
    ).status_code == 200
    assert ana.patch(f"/api/v1/places/{place['id']}", json={"name": "X"}).status_code == 200


def test_trip_must_keep_account_traveler(two_families):
    bob = two_families["bob"]
    trip = bob.post("/api/v1/trips", json={"name": "Solo"}).json()
    bob_traveler_id = trip["travelers"][0]["id"]
    # quitarse a sí mismo dejaría el viaje huérfano → 409
    resp = bob.delete(f"/api/v1/trips/{trip['id']}/travelers/{bob_traveler_id}")
    assert resp.status_code == 409
    assert bob.patch(
        f"/api/v1/trips/{trip['id']}", json={"traveler_ids": []}
    ).status_code == 409
    # con un virtual no basta: hace falta alguien con cuenta
    virtual = bob.post("/api/v1/travelers", json={"name": "Peque"}).json()
    assert bob.patch(
        f"/api/v1/trips/{trip['id']}", json={"traveler_ids": [virtual["id"]]}
    ).status_code == 409


def test_categories_scoped_per_family(two_families):
    bob, ana = two_families["bob"], two_families["ana"]
    bob.post("/api/v1/categories?kind=expense", json={"kind": "expense", "name": "Buceo"})
    ana_names = [c["name"] for c in ana.get("/api/v1/categories?kind=expense").json()]
    assert "Buceo" not in ana_names

    # renombrar "Comida" en la familia B no toca los gastos de la familia A
    trip = bob.post("/api/v1/trips", json={"name": "Gastos"}).json()
    expense = bob.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-07-01", "description": "Ramen", "amount": 10, "category": "Comida"},
    ).json()
    ana_comida = next(
        c for c in ana.get("/api/v1/categories?kind=expense").json() if c["name"] == "Comida"
    )
    assert ana.patch(
        f"/api/v1/categories/{ana_comida['id']}", json={"name": "Manduca"}
    ).status_code == 200
    refreshed = bob.get(f"/api/v1/trips/{trip['id']}/expenses").json()
    assert refreshed[0]["category"] == "Comida"
    # y bob no puede tocar las categorías de la familia B
    assert bob.patch(
        f"/api/v1/categories/{ana_comida['id']}", json={"color": "#000000"}
    ).status_code == 403
    assert expense  # (documenta que el gasto de A sobrevive intacto)


def test_guest_sees_trip_family_categories(two_families):
    bob, ana = two_families["bob"], two_families["ana"]
    bob.post("/api/v1/categories?kind=expense", json={"kind": "expense", "name": "Buceo"})
    trip = bob.post("/api/v1/trips", json={"name": "Conjunto"}).json()
    ana_traveler = _me_traveler(ana)
    bob.post(f"/api/v1/trips/{trip['id']}/travelers/{ana_traveler['id']}")
    # con ?trip_id=, la invitada ve las categorías de la familia del viaje
    names = [
        c["name"]
        for c in ana.get(f"/api/v1/categories?kind=expense&trip_id={trip['id']}").json()
    ]
    assert "Buceo" in names


def test_packing_templates_family_read_owner_write(app, two_families):
    """Plantillas: toda tu familia las VE; las EDITA su dueño (o todos si es virtual)."""
    client, bob, ana = two_families["admin"], two_families["bob"], two_families["ana"]
    make_user(client, "carl", family_id=two_families["family_a"])
    carl = login(app, "carl")

    template = bob.post("/api/v1/packing-templates", json={"name": "Playa"}).json()
    assert template["traveler_id"] == _me_traveler(bob)["id"]
    # carl (misma familia): la ve y la consulta, pero no la toca
    assert template["id"] in [t["id"] for t in carl.get("/api/v1/packing-templates").json()]
    assert carl.get(f"/api/v1/packing-templates/{template['id']}").status_code == 200
    assert carl.patch(
        f"/api/v1/packing-templates/{template['id']}", json={"name": "X"}
    ).status_code == 403
    assert carl.delete(f"/api/v1/packing-templates/{template['id']}").status_code == 403
    assert carl.post(
        f"/api/v1/packing-templates/{template['id']}/items", json={"name": "Crema"}
    ).status_code == 403
    # ana (otra familia): ni la ve ni la consulta
    assert template["id"] not in [t["id"] for t in ana.get("/api/v1/packing-templates").json()]
    assert ana.get(f"/api/v1/packing-templates/{template['id']}").status_code == 403
    # mismo nombre en otro dueño: permitido (unique por viajero); repetido → 409
    assert carl.post("/api/v1/packing-templates", json={"name": "Playa"}).status_code == 201
    assert bob.post("/api/v1/packing-templates", json={"name": "playa"}).status_code == 409

    # la de un virtual de la familia la gestionan todos sus usuarios
    peque = bob.post("/api/v1/travelers", json={"name": "Peque"}).json()
    shared = bob.post(
        "/api/v1/packing-templates", json={"name": "Cole", "traveler_id": peque["id"]}
    ).json()
    assert shared["traveler_id"] == peque["id"]
    assert carl.post(
        f"/api/v1/packing-templates/{shared['id']}/items", json={"name": "Mochila"}
    ).status_code == 201
    # otra familia ni la ve ni puede crear plantillas de ese virtual
    assert ana.get(f"/api/v1/packing-templates/{shared['id']}").status_code == 403
    assert ana.post(
        "/api/v1/packing-templates", json={"name": "X", "traveler_id": peque["id"]}
    ).status_code == 403
    # tampoco puedes crear plantillas a nombre de otro usuario de tu familia
    assert carl.post(
        "/api/v1/packing-templates",
        json={"name": "Ajena", "traveler_id": _me_traveler(bob)["id"]},
    ).status_code == 403
    # el admin accede a cualquiera por id y su lista las incluye TODAS
    foreign = ana.post("/api/v1/packing-templates", json={"name": "Suya"}).json()
    assert client.get(f"/api/v1/packing-templates/{foreign['id']}").status_code == 200
    admin_list = [t["id"] for t in client.get("/api/v1/packing-templates").json()]
    assert {template["id"], shared["id"], foreign["id"]} <= set(admin_list)


def test_bag_family_visibility_and_edit(app, two_families):
    """En el viaje: ver = editar. Tu familia entera sí; otras familias ni se ven."""
    client, bob, ana = two_families["admin"], two_families["bob"], two_families["ana"]
    make_user(client, "carl", family_id=two_families["family_a"])
    carl = login(app, "carl")
    carl_traveler = _me_traveler(carl)
    bob_traveler = _me_traveler(bob)
    ana_traveler = _me_traveler(ana)

    trip = bob.post("/api/v1/trips", json={"name": "Nieve"}).json()
    for traveler_id in (carl_traveler["id"], ana_traveler["id"]):
        bob.post(f"/api/v1/trips/{trip['id']}/travelers/{traveler_id}")
    peque = bob.post("/api/v1/travelers", json={"name": "Peque"}).json()
    bob.post(f"/api/v1/trips/{trip['id']}/travelers/{peque['id']}")

    packing = f"/api/v1/trips/{trip['id']}/packing"
    # carl edita la suya, la común, la del virtual Y la de bob (misma familia)
    assert carl.post(packing, json={"name": "Guantes", "traveler_id": carl_traveler["id"]}).status_code == 201
    assert carl.post(packing, json={"name": "Botiquín"}).status_code == 201
    assert carl.post(packing, json={"name": "Trineo", "traveler_id": peque["id"]}).status_code == 201
    assert carl.post(packing, json={"name": "Gorro", "traveler_id": bob_traveler["id"]}).status_code == 201
    item = next(i for i in carl.get(packing).json() if i["name"] == "Gorro")
    assert bob.patch(f"/api/v1/packing/{item['id']}", json={"checked": True}).status_code == 200

    # ana (otra familia): la suya y la común sí; las de la familia A no
    assert ana.post(packing, json={"name": "Esquís", "traveler_id": ana_traveler["id"]}).status_code == 201
    assert ana.post(packing, json={"name": "Mapa"}).status_code == 201
    assert ana.post(packing, json={"name": "Nada", "traveler_id": bob_traveler["id"]}).status_code == 403
    assert ana.post(packing, json={"name": "Nada", "traveler_id": peque["id"]}).status_code == 403
    assert ana.patch(f"/api/v1/packing/{item['id']}", json={"checked": False}).status_code == 403
    # ni siquiera las VE: su lista es la común + su familia
    ana_names = {i["name"] for i in ana.get(packing).json()}
    assert ana_names == {"Botiquín", "Mapa", "Esquís"}
    # y la familia A no ve la maleta de ana
    carl_names = {i["name"] for i in carl.get(packing).json()}
    assert "Esquís" not in carl_names and "Mapa" in carl_names
    # mover un elemento propio a una maleta de otra familia tampoco
    own_item = next(i for i in ana.get(packing).json() if i["name"] == "Esquís")
    assert ana.patch(
        f"/api/v1/packing/{own_item['id']}", json={"traveler_id": peque["id"]}
    ).status_code == 403
    # el admin lo ve y lo edita todo
    admin_names = {i["name"] for i in client.get(packing).json()}
    assert {"Guantes", "Gorro", "Esquís", "Mapa"} <= admin_names
    assert client.patch(f"/api/v1/packing/{own_item['id']}", json={"checked": True}).status_code == 200


def test_template_reassign_admin_only(app, two_families):
    client, bob, ana = two_families["admin"], two_families["bob"], two_families["ana"]
    template = bob.post("/api/v1/packing-templates", json={"name": "Playa"}).json()
    ana_tid = _me_traveler(ana)["id"]
    # ni el propio dueño puede reasignar: mover maletas entre viajeros es del admin
    assert bob.patch(
        f"/api/v1/packing-templates/{template['id']}", json={"traveler_id": ana_tid}
    ).status_code == 403
    resp = client.patch(
        f"/api/v1/packing-templates/{template['id']}", json={"traveler_id": ana_tid}
    )
    assert resp.status_code == 200 and resp.json()["traveler_id"] == ana_tid
    # la plantilla cambia de familia: ana la ve, bob ya no
    assert template["id"] in [t["id"] for t in ana.get("/api/v1/packing-templates").json()]
    assert bob.get(f"/api/v1/packing-templates/{template['id']}").status_code == 403
    # renombrar sin tocar el dueño sigue funcionando (payload solo con name)
    assert ana.patch(
        f"/api/v1/packing-templates/{template['id']}", json={"name": "Costa"}
    ).status_code == 200
    # choque de nombre en el dueño destino → 409
    other = bob.post("/api/v1/packing-templates", json={"name": "Costa"}).json()
    assert client.patch(
        f"/api/v1/packing-templates/{other['id']}", json={"traveler_id": ana_tid}
    ).status_code == 409


def test_template_apply_and_sync_permissions(app, two_families):
    client, bob, ana = two_families["admin"], two_families["bob"], two_families["ana"]
    make_user(client, "carl", family_id=two_families["family_a"])
    carl = login(app, "carl")
    carl_traveler = _me_traveler(carl)
    bob_traveler = _me_traveler(bob)

    trip = bob.post("/api/v1/trips", json={"name": "Costa"}).json()
    bob.post(f"/api/v1/trips/{trip['id']}/travelers/{carl_traveler['id']}")
    bob.post(f"/api/v1/trips/{trip['id']}/travelers/{_me_traveler(ana)['id']}")
    template = carl.post("/api/v1/packing-templates", json={"name": "Base"}).json()
    carl.post(f"/api/v1/packing-templates/{template['id']}/items", json={"name": "Toalla"})

    apply_url = f"/api/v1/trips/{trip['id']}/packing/apply/{template['id']}"
    # carl aplica sobre la suya, la común Y la de bob (familia = editable)
    assert carl.post(f"{apply_url}?traveler_id={carl_traveler['id']}").status_code == 200
    assert carl.post(apply_url).status_code == 200
    assert carl.post(f"{apply_url}?traveler_id={bob_traveler['id']}").status_code == 200
    # bob puede APLICAR la plantilla de carl (lectura familiar)…
    assert bob.post(f"{apply_url}?traveler_id={bob_traveler['id']}").status_code == 200
    # …pero no sincronizarla (escritura solo del dueño)
    assert bob.post(
        f"/api/v1/packing-templates/{template['id']}/sync-from-trip/{trip['id']}"
    ).status_code == 403
    # ana (otra familia) ni la lee ni la aplica, ni siquiera sobre su propia maleta
    assert ana.post(f"{apply_url}?traveler_id={_me_traveler(ana)['id']}").status_code == 403
    # guardar la maleta de OTRO usuario como plantilla → el dueño sería él: 403
    assert carl.post(
        "/api/v1/packing-templates",
        json={"name": "Robada", "from_trip_id": trip["id"], "traveler_id": bob_traveler["id"]},
    ).status_code == 403
    # la común guardada como plantilla nace del propio usuario
    saved = carl.post(
        "/api/v1/packing-templates", json={"name": "Común", "from_trip_id": trip["id"]}
    ).json()
    assert saved["traveler_id"] == carl_traveler["id"]
    # sync de su plantilla desde la común: OK
    assert carl.post(
        f"/api/v1/packing-templates/{template['id']}/sync-from-trip/{trip['id']}"
    ).status_code == 200
    # desvincular la plantilla de la común: la selección se va, los items quedan
    items_before = len(carl.get(f"/api/v1/trips/{trip['id']}/packing").json())
    assert carl.delete(f"/api/v1/trips/{trip['id']}/packing/selection").status_code == 204
    selections = carl.get(f"/api/v1/trips/{trip['id']}/packing/selections").json()
    assert all(s["traveler_id"] is not None for s in selections)
    assert len(carl.get(f"/api/v1/trips/{trip['id']}/packing").json()) == items_before
    # ana no puede desvincular maletas de otra familia
    assert ana.delete(
        f"/api/v1/trips/{trip['id']}/packing/selection?traveler_id={bob_traveler['id']}"
    ).status_code == 403


def test_world_map_per_family_with_shared_trip(two_families):
    bob, ana = two_families["bob"], two_families["ana"]
    # viaje TERMINADO de la familia A con ana (familia B) como invitada
    trip = bob.post(
        "/api/v1/trips",
        json={"name": "Japón", "countries": ["JP"], "start_date": "2020-01-01", "end_date": "2020-01-10"},
    ).json()
    bob_map = [w["country_code"] for w in bob.get("/api/v1/world-places").json()]
    assert "JP" in bob_map
    # ana aún no participa: su mapa no lo cuenta
    ana_map = [w["country_code"] for w in ana.get("/api/v1/world-places").json()]
    assert "JP" not in ana_map
    # al participar, el viaje conjunto alimenta también el mapa de su familia
    ana_traveler = _me_traveler(ana)
    bob.post(f"/api/v1/trips/{trip['id']}/travelers/{ana_traveler['id']}")
    ana_map = [w["country_code"] for w in ana.get("/api/v1/world-places").json()]
    assert "JP" in ana_map
    # y las entradas de una familia no son editables por la otra
    bob_entry = next(w for w in bob.get("/api/v1/world-places").json() if w["country_code"] == "JP")
    assert ana.delete(f"/api/v1/world-places/{bob_entry['id']}").status_code == 403


def test_user_without_family_cannot_create_trip(app, client):
    # make_user sin family_id crea el viajero sin familia
    make_user(client, "solo", traveler_name="Solo")
    solo = login(app, "solo")
    resp = solo.post("/api/v1/trips", json={"name": "Nada"})
    assert resp.status_code == 403
    assert "familia" in resp.json()["detail"]
    # el mapa devuelve vacío en vez de error
    assert solo.get("/api/v1/world-places").json() == []


def test_traveler_create_family_permissions(two_families):
    admin, ana = two_families["admin"], two_families["ana"]
    fam_a, fam_b = two_families["family_a"], two_families["family_b"]
    # sin campo → familia del creador
    implicit = ana.post("/api/v1/travelers", json={"name": "Implícito"}).json()
    assert implicit["family_id"] == fam_b
    # explícita: la suya o ninguna sí; la de otros no (el admin sí)
    own = ana.post("/api/v1/travelers", json={"name": "Propio", "family_id": fam_b}).json()
    assert own["family_id"] == fam_b
    none = ana.post("/api/v1/travelers", json={"name": "Libre", "family_id": None}).json()
    assert none["family_id"] is None
    assert ana.post(
        "/api/v1/travelers", json={"name": "Intruso", "family_id": fam_a}
    ).status_code == 403
    cross = admin.post(
        "/api/v1/travelers", json={"name": "DeOtra", "family_id": fam_b}
    ).json()
    assert cross["family_id"] == fam_b


def test_traveler_with_account_cannot_be_deleted(client):
    make_user(client, "ana", traveler_name="Ana")
    traveler = next(t for t in client.get("/api/v1/travelers").json() if t["name"] == "Ana")
    assert client.delete(f"/api/v1/travelers/{traveler['id']}").status_code == 409


def test_traveler_edit_permissions(app, client):
    make_user(client, "ana", traveler_name="Ana")
    make_user(client, "bob", traveler_name="Bob")
    ana, bob = login(app, "ana"), login(app, "bob")
    ana_traveler = _me_traveler(ana)
    # su propio viajero sí; el de otro usuario no (el admin sí)
    assert ana.patch(
        f"/api/v1/travelers/{ana_traveler['id']}", json={"color": "#0ea5e9"}
    ).status_code == 200
    assert bob.patch(
        f"/api/v1/travelers/{ana_traveler['id']}", json={"color": "#000000"}
    ).status_code == 403
    assert client.patch(
        f"/api/v1/travelers/{ana_traveler['id']}", json={"color": "#16a34a"}
    ).status_code == 200
    # los virtuales los puede editar cualquiera
    virtual = bob.post("/api/v1/travelers", json={"name": "Peque"}).json()
    assert ana.patch(
        f"/api/v1/travelers/{virtual['id']}", json={"color": "#e11d48"}
    ).status_code == 200
