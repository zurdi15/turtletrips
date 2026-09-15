from conftest import login, make_user


def _make_trip(client) -> int:
    return client.post("/api/v1/trips", json={"name": "Camboya"}).json()["id"]


def test_links_crud_and_groups(client):
    trip_id = _make_trip(client)

    group = client.post(f"/api/v1/trips/{trip_id}/link-groups", json={"name": " Alojamientos "})
    assert group.status_code == 201, group.text
    group = group.json()
    assert group["name"] == "Alojamientos"
    assert group["position"] == 0

    link = client.post(
        f"/api/v1/trips/{trip_id}/links",
        json={
            "title": "Hotel candidato",
            "url": "booking.com/hotel/kh/angkor",
            "notes": "cerca del centro",
            "group_id": group["id"],
        },
    )
    assert link.status_code == 201, link.text
    link = link.json()
    # sin esquema se antepone https://
    assert link["url"] == "https://booking.com/hotel/kh/angkor"
    assert link["group_id"] == group["id"]
    assert link["position"] == 0

    loose = client.post(
        f"/api/v1/trips/{trip_id}/links",
        json={"title": "Visado Camboya", "url": "https://www.evisa.gov.kh/"},
    ).json()
    assert loose["group_id"] is None

    listed = client.get(f"/api/v1/trips/{trip_id}/links").json()
    assert [l["title"] for l in listed] == ["Hotel candidato", "Visado Camboya"]
    assert [g["name"] for g in client.get(f"/api/v1/trips/{trip_id}/link-groups").json()] == [
        "Alojamientos"
    ]

    # patch parcial: no toca el resto de campos
    resp = client.patch(f"/api/v1/links/{link['id']}", json={"notes": None})
    assert resp.status_code == 200
    assert resp.json()["notes"] is None
    assert resp.json()["url"] == "https://booking.com/hotel/kh/angkor"

    resp = client.patch(f"/api/v1/link-groups/{group['id']}", json={"name": "Hoteles"})
    assert resp.json()["name"] == "Hoteles"

    # borrar el bloque deja sus enlaces sin bloque, no los borra
    assert client.delete(f"/api/v1/link-groups/{group['id']}").status_code == 204
    listed = client.get(f"/api/v1/trips/{trip_id}/links").json()
    assert len(listed) == 2
    assert all(l["group_id"] is None for l in listed)

    assert client.delete(f"/api/v1/links/{link['id']}").status_code == 204
    assert len(client.get(f"/api/v1/trips/{trip_id}/links").json()) == 1
    assert client.patch(f"/api/v1/links/{link['id']}", json={}).status_code == 404


def test_links_validation(client):
    trip_id = _make_trip(client)
    assert (
        client.post(f"/api/v1/trips/{trip_id}/links", json={"title": "", "url": "x.com"}).status_code
        == 422
    )
    assert (
        client.post(
            f"/api/v1/trips/{trip_id}/links", json={"title": "Sin url", "url": "   "}
        ).status_code
        == 422
    )
    assert (
        client.post(f"/api/v1/trips/{trip_id}/link-groups", json={"name": ""}).status_code == 422
    )


def test_link_group_must_belong_to_trip(client):
    trip_a = _make_trip(client)
    trip_b = _make_trip(client)
    group_b = client.post(f"/api/v1/trips/{trip_b}/link-groups", json={"name": "B"}).json()

    resp = client.post(
        f"/api/v1/trips/{trip_a}/links",
        json={"title": "x", "url": "https://x.example", "group_id": group_b["id"]},
    )
    assert resp.status_code == 400

    link_a = client.post(
        f"/api/v1/trips/{trip_a}/links", json={"title": "x", "url": "https://x.example"}
    ).json()
    resp = client.patch(f"/api/v1/links/{link_a['id']}", json={"group_id": group_b["id"]})
    assert resp.status_code == 400
    resp = client.patch(f"/api/v1/links/{link_a['id']}", json={"group_id": 9999})
    assert resp.status_code == 400


def test_links_reorder_and_move_between_groups(client):
    trip_id = _make_trip(client)
    g1 = client.post(f"/api/v1/trips/{trip_id}/link-groups", json={"name": "Uno"}).json()
    g2 = client.post(f"/api/v1/trips/{trip_id}/link-groups", json={"name": "Dos"}).json()
    assert g2["position"] == 1

    ids = [
        client.post(
            f"/api/v1/trips/{trip_id}/links",
            json={"title": f"L{i}", "url": f"https://l{i}.example", "group_id": g1["id"]},
        ).json()["id"]
        for i in range(3)
    ]
    # posiciones consecutivas dentro del bloque
    positions = [l["position"] for l in client.get(f"/api/v1/trips/{trip_id}/links").json()]
    assert positions == [0, 1, 2]

    # cambiar de bloque por PATCH manda el enlace al final del nuevo
    moved = client.patch(f"/api/v1/links/{ids[0]}", json={"group_id": g2["id"]}).json()
    assert moved["group_id"] == g2["id"]
    assert moved["position"] == 0

    # disposición completa tras un drag & drop: L2 pasa a "sin bloque",
    # L1 queda solo en Uno y L0 en Dos
    resp = client.post(
        f"/api/v1/trips/{trip_id}/links/reorder",
        json={
            "buckets": [
                {"group_id": g1["id"], "ids": [ids[1]]},
                {"group_id": g2["id"], "ids": [ids[0]]},
                {"group_id": None, "ids": [ids[2]]},
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    by_id = {l["id"]: l for l in resp.json()}
    assert by_id[ids[2]]["group_id"] is None
    assert by_id[ids[1]]["group_id"] == g1["id"]
    assert by_id[ids[0]]["group_id"] == g2["id"]

    # reordenar bloques: Dos delante de Uno
    resp = client.post(
        f"/api/v1/trips/{trip_id}/link-groups/reorder", json={"ids": [g2["id"], g1["id"]]}
    )
    assert resp.status_code == 204
    names = [g["name"] for g in client.get(f"/api/v1/trips/{trip_id}/link-groups").json()]
    assert names == ["Dos", "Uno"]


def test_links_cascade_on_trip_delete(client, db_session):
    from app.models import LinkGroup, TripLink

    trip_id = _make_trip(client)
    group = client.post(f"/api/v1/trips/{trip_id}/link-groups", json={"name": "eSIM"}).json()
    client.post(
        f"/api/v1/trips/{trip_id}/links",
        json={"title": "Blog eSIM", "url": "https://blog.example", "group_id": group["id"]},
    )
    client.delete(f"/api/v1/trips/{trip_id}")
    assert db_session.query(TripLink).count() == 0
    assert db_session.query(LinkGroup).count() == 0


def test_links_require_trip_membership(app, client):
    trip_id = _make_trip(client)
    link = client.post(
        f"/api/v1/trips/{trip_id}/links", json={"title": "x", "url": "https://x.example"}
    ).json()
    group = client.post(f"/api/v1/trips/{trip_id}/link-groups", json={"name": "G"}).json()

    make_user(client, "guest")
    guest = login(app, "guest")
    assert guest.get(f"/api/v1/trips/{trip_id}/links").status_code == 403
    assert guest.get(f"/api/v1/trips/{trip_id}/link-groups").status_code == 403
    assert guest.patch(f"/api/v1/links/{link['id']}", json={"title": "y"}).status_code == 403
    assert guest.delete(f"/api/v1/link-groups/{group['id']}").status_code == 403
    assert (
        guest.post(
            f"/api/v1/trips/{trip_id}/links/reorder", json={"buckets": []}
        ).status_code
        == 403
    )
