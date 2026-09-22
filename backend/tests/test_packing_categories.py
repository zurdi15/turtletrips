def test_default_categories_seeded(client):
    expense = [c["name"] for c in client.get("/api/v1/categories?kind=expense").json()]
    assert expense == [
        "Comida", "Transporte", "Alojamiento", "Tours", "Entradas",
        "Souvenirs", "Gasolina", "Vuelos", "Otros",
    ]
    packing = [c["name"] for c in client.get("/api/v1/categories?kind=packing").json()]
    assert packing == ["Botiquín", "Ropa", "Tecnología"]


def test_category_crud_and_rename_propagates(client, trip):
    created = client.post(
        "/api/v1/categories", json={"kind": "expense", "name": "Cafés", "color": "#000000"}
    )
    assert created.status_code == 201

    # duplicado -> 409
    assert (
        client.post("/api/v1/categories", json={"kind": "expense", "name": "cafés"}).status_code
        == 409
    )

    expense = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={"day": "2026-04-01", "description": "Latte", "amount": "4", "category": "Cafés"},
    ).json()

    # renombrar actualiza los gastos existentes
    resp = client.patch(
        f"/api/v1/categories/{created.json()['id']}", json={"name": "Cafetería"}
    )
    assert resp.json()["name"] == "Cafetería"
    assert (
        client.get(f"/api/v1/trips/{trip['id']}/expenses").json()[0]["category"] == "Cafetería"
    )

    # borrar la categoría no toca los gastos
    assert client.delete(f"/api/v1/categories/{created.json()['id']}").status_code == 204
    assert (
        client.get(f"/api/v1/trips/{trip['id']}/expenses").json()[0]["category"] == "Cafetería"
    )
    assert expense["id"] is not None


def test_packing_crud(client, trip):
    trip_id = trip["id"]
    item = client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "Ibuprofeno", "category": "Botiquín"},
    ).json()
    client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "Adaptador de enchufe", "category": "Tecnología", "url": "https://amzn.example/adapter"},
    )

    items = client.get(f"/api/v1/trips/{trip_id}/packing").json()
    assert len(items) == 2
    assert items[1]["url"] == "https://amzn.example/adapter"

    # marcar como hecho
    resp = client.patch(f"/api/v1/packing/{item['id']}", json={"checked": True})
    assert resp.json()["checked"] is True

    assert client.delete(f"/api/v1/packing/{item['id']}").status_code == 204
    assert len(client.get(f"/api/v1/trips/{trip_id}/packing").json()) == 1


def test_packing_template_save_and_reuse(client, trip):
    trip_id = trip["id"]
    client.post(f"/api/v1/trips/{trip_id}/packing", json={"name": "Pasaporte", "category": "Ropa"})
    client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "Cargador", "category": "Tecnología", "checked": True},
    )

    # guardar la maleta del viaje como plantilla
    template = client.post(
        "/api/v1/packing-templates", json={"name": "Básica", "from_trip_id": trip_id}
    ).json()
    assert template["item_count"] == 2

    listed = client.get("/api/v1/packing-templates").json()
    assert [t["name"] for t in listed] == ["Básica"]

    # aplicarla a otro viaje: los elementos llegan sin marcar
    other = client.post("/api/v1/trips", json={"name": "Otro"}).json()
    items = client.post(f"/api/v1/trips/{other['id']}/packing/apply/{template['id']}").json()
    assert len(items) == 2
    assert all(not i["checked"] for i in items)

    # aplicar dos veces no duplica
    items = client.post(f"/api/v1/trips/{other['id']}/packing/apply/{template['id']}").json()
    assert len(items) == 2

    assert client.delete(f"/api/v1/packing-templates/{template['id']}").status_code == 204
    assert client.get("/api/v1/packing-templates").json() == []


def test_packing_per_traveler(client, trip):
    from conftest import add_traveler

    trip_id = trip["id"]
    romm = add_traveler(client, trip_id, "Romm")
    ana = add_traveler(client, trip_id, "Ana")

    # maleta común + maleta de cada viajero
    client.post(f"/api/v1/trips/{trip_id}/packing", json={"name": "Botiquín común", "category": "Botiquín"})
    client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "Camisetas", "category": "Ropa", "traveler_id": romm["id"]},
    )
    resp = client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "Vestido", "category": "Ropa", "traveler_id": ana["id"]},
    )
    assert resp.status_code == 201

    # viajero que no está en el viaje -> 400
    other_traveler = client.post("/api/v1/travelers", json={"name": "Externo"}).json()
    resp = client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "X", "traveler_id": other_traveler["id"]},
    )
    assert resp.status_code == 400

    items = client.get(f"/api/v1/trips/{trip_id}/packing").json()
    by_traveler = {}
    for i in items:
        by_traveler.setdefault(i["traveler_id"], []).append(i["name"])
    assert by_traveler[None] == ["Botiquín común"]
    assert by_traveler[romm["id"]] == ["Camisetas"]
    assert by_traveler[ana["id"]] == ["Vestido"]

    # plantilla desde la maleta de Romm -> solo sus elementos, y queda seleccionada
    template = client.post(
        "/api/v1/packing-templates",
        json={"name": "De Romm", "from_trip_id": trip_id, "traveler_id": romm["id"]},
    ).json()
    assert template["item_count"] == 1

    selections = client.get(f"/api/v1/trips/{trip_id}/packing/selections").json()
    assert {"traveler_id": romm["id"], "template_id": template["id"]} in selections

    # aplicar la plantilla a la maleta de Ana: copia sin tocar la de Romm ni la plantilla
    client.post(
        f"/api/v1/trips/{trip_id}/packing/apply/{template['id']}?traveler_id={ana['id']}"
    )
    items = client.get(f"/api/v1/trips/{trip_id}/packing").json()
    ana_items = sorted(i["name"] for i in items if i["traveler_id"] == ana["id"])
    assert ana_items == ["Camisetas", "Vestido"]
    selections = client.get(f"/api/v1/trips/{trip_id}/packing/selections").json()
    assert {"traveler_id": ana["id"], "template_id": template["id"]} in selections

    # sync de la maleta de Ana (con overrides) de vuelta a la plantilla
    detail = client.post(
        f"/api/v1/packing-templates/{template['id']}/sync-from-trip/{trip_id}?traveler_id={ana['id']}"
    ).json()
    assert sorted(i["name"] for i in detail["items"]) == ["Camisetas", "Vestido"]


def test_template_edit_and_sync(client, trip):
    trip_id = trip["id"]
    # plantilla vacía creada desde cero y editada directamente
    template = client.post("/api/v1/packing-templates", json={"name": "Montaña"}).json()
    assert template["item_count"] == 0

    item = client.post(
        f"/api/v1/packing-templates/{template['id']}/items",
        json={"name": "Frontal", "category": "Tecnología"},
    ).json()
    client.post(
        f"/api/v1/packing-templates/{template['id']}/items",
        json={"name": "Botas", "category": "Ropa"},
    )
    detail = client.get(f"/api/v1/packing-templates/{template['id']}").json()
    assert [i["name"] for i in detail["items"]] == ["Frontal", "Botas"]

    resp = client.patch(
        f"/api/v1/packing-template-items/{item['id']}",
        json={"url": "https://example.com/frontal"},
    )
    assert resp.json()["url"] == "https://example.com/frontal"

    assert client.delete(f"/api/v1/packing-template-items/{item['id']}").status_code == 204

    # renombrar plantilla
    resp = client.patch(f"/api/v1/packing-templates/{template['id']}", json={"name": "Trekking"})
    assert resp.json()["name"] == "Trekking"

    # sincronizar desde la maleta de un viaje sobrescribe los elementos
    client.post(f"/api/v1/trips/{trip_id}/packing", json={"name": "Crema solar", "category": "Botiquín"})
    client.post(f"/api/v1/trips/{trip_id}/packing", json={"name": "Gorra", "category": "Ropa"})
    detail = client.post(
        f"/api/v1/packing-templates/{template['id']}/sync-from-trip/{trip_id}"
    ).json()
    assert sorted(i["name"] for i in detail["items"]) == ["Crema solar", "Gorra"]


def test_packing_quantity(client, trip):
    trip_id = trip["id"]
    # sin cantidad = 1 unidad; con ella, un único elemento de N unidades
    single = client.post(
        f"/api/v1/trips/{trip_id}/packing", json={"name": "Gorra", "category": "Ropa"}
    ).json()
    assert single["quantity"] == 1
    shirts = client.post(
        f"/api/v1/trips/{trip_id}/packing",
        json={"name": "Camisetas", "category": "Ropa", "quantity": 4},
    ).json()
    assert shirts["quantity"] == 4

    resp = client.patch(f"/api/v1/packing/{shirts['id']}", json={"quantity": 5})
    assert resp.json()["quantity"] == 5
    # marcar no toca la cantidad
    resp = client.patch(f"/api/v1/packing/{shirts['id']}", json={"checked": True})
    assert resp.json()["quantity"] == 5

    # fuera de rango -> 422 (ni cero ni negativos; tope 99)
    for bad in (0, -1, 100):
        resp = client.patch(f"/api/v1/packing/{shirts['id']}", json={"quantity": bad})
        assert resp.status_code == 422
        resp = client.post(
            f"/api/v1/trips/{trip_id}/packing",
            json={"name": "Calcetines", "category": "Ropa", "quantity": bad},
        )
        assert resp.status_code == 422

    # la cantidad viaja a la plantilla y de vuelta a otro viaje
    template = client.post(
        "/api/v1/packing-templates", json={"name": "Ropa", "from_trip_id": trip_id}
    ).json()
    detail = client.get(f"/api/v1/packing-templates/{template['id']}").json()
    assert {i["name"]: i["quantity"] for i in detail["items"]} == {"Gorra": 1, "Camisetas": 5}

    other = client.post("/api/v1/trips", json={"name": "Otro"}).json()
    items = client.post(f"/api/v1/trips/{other['id']}/packing/apply/{template['id']}").json()
    assert {i["name"]: i["quantity"] for i in items} == {"Gorra": 1, "Camisetas": 5}

    # items de plantilla: alta con cantidad, edición y sync desde la maleta
    item = client.post(
        f"/api/v1/packing-templates/{template['id']}/items",
        json={"name": "Pantalones", "category": "Ropa", "quantity": 2},
    ).json()
    assert item["quantity"] == 2
    resp = client.patch(f"/api/v1/packing-template-items/{item['id']}", json={"quantity": 3})
    assert resp.json()["quantity"] == 3
    assert (
        client.patch(
            f"/api/v1/packing-template-items/{item['id']}", json={"quantity": 0}
        ).status_code
        == 422
    )

    client.patch(f"/api/v1/packing/{single['id']}", json={"quantity": 2})
    detail = client.post(
        f"/api/v1/packing-templates/{template['id']}/sync-from-trip/{trip_id}"
    ).json()
    assert {i["name"]: i["quantity"] for i in detail["items"]} == {"Gorra": 2, "Camisetas": 5}
