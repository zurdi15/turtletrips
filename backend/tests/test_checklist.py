def _make_trip(client) -> int:
    return client.post("/api/v1/trips", json={"name": "Japón"}).json()["id"]


def test_checklist_crud(client):
    trip_id = _make_trip(client)

    item = client.post(
        f"/api/v1/trips/{trip_id}/checklist",
        json={
            "title": "Sacar el visado",
            "due_date": "2026-03-01",
            "url": "https://embajada.example/visado",
            "notes": "web embajada",
        },
    )
    assert item.status_code == 201
    item = item.json()
    assert item["done"] is False
    assert item["due_date"] == "2026-03-01"
    assert item["url"] == "https://embajada.example/visado"

    client.post(f"/api/v1/trips/{trip_id}/checklist", json={"title": "Check-in online"})
    listed = client.get(f"/api/v1/trips/{trip_id}/checklist").json()
    assert [i["title"] for i in listed] == ["Sacar el visado", "Check-in online"]

    resp = client.patch(f"/api/v1/checklist-items/{item['id']}", json={"done": True})
    assert resp.json()["done"] is True
    # el patch parcial no toca el resto de campos
    assert resp.json()["due_date"] == "2026-03-01"

    assert client.delete(f"/api/v1/checklist-items/{item['id']}").status_code == 204
    assert len(client.get(f"/api/v1/trips/{trip_id}/checklist").json()) == 1
    assert client.patch(f"/api/v1/checklist-items/{item['id']}", json={}).status_code == 404


def test_checklist_requires_title(client):
    trip_id = _make_trip(client)
    resp = client.post(f"/api/v1/trips/{trip_id}/checklist", json={"title": ""})
    assert resp.status_code == 422


def test_checklist_cascade_on_trip_delete(client, db_session):
    from app.models import ChecklistItem

    trip_id = _make_trip(client)
    client.post(f"/api/v1/trips/{trip_id}/checklist", json={"title": "Seguro de viaje"})
    client.delete(f"/api/v1/trips/{trip_id}")
    assert db_session.query(ChecklistItem).count() == 0
