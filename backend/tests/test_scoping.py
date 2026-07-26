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


def test_packing_templates_scoped_per_family(two_families):
    bob, ana = two_families["bob"], two_families["ana"]
    template = bob.post("/api/v1/packing-templates", json={"name": "Playa"}).json()
    assert ana.get("/api/v1/packing-templates").json() == []
    assert ana.get(f"/api/v1/packing-templates/{template['id']}").status_code == 403
    assert ana.delete(f"/api/v1/packing-templates/{template['id']}").status_code == 403
    # mismo nombre en otra familia: permitido (unique por familia)
    assert ana.post("/api/v1/packing-templates", json={"name": "Playa"}).status_code == 201


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
