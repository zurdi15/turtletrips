import io

from conftest import add_traveler


def test_export_import_roundtrip(client, trip):
    trip_id = trip["id"]
    traveler = add_traveler(client, trip_id, "Romm")
    client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        json={
            "day": "2026-04-01", "description": "Cena", "amount": "40.50",
            "category": "Comida", "paid_by_id": traveler["id"],
        },
    )
    client.post(
        f"/api/v1/trips/{trip_id}/expenses",
        json={
            "day": "2026-04-02", "description": "Tren", "amount": "5000",
            "currency": "JPY", "exchange_rate": "0.006", "category": "Transporte",
        },
    )

    resp = client.get(f"/api/v1/trips/{trip_id}/expenses/export.csv")
    assert resp.status_code == 200
    csv_content = resp.content

    # importar en un segundo viaje
    other = client.post(
        "/api/v1/trips", json={"name": "Copia", "base_currency": "EUR"}
    ).json()

    resp = client.post(
        f"/api/v1/trips/{other['id']}/expenses/import?dry_run=true",
        files={"file": ("gastos.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert resp.status_code == 200
    preview = resp.json()
    assert preview["dry_run"] is True
    assert len(preview["valid_rows"]) == 2
    assert preview["errors"] == []
    assert preview["imported"] == 0
    # dry-run no crea nada
    assert client.get(f"/api/v1/trips/{other['id']}/expenses").json() == []

    resp = client.post(
        f"/api/v1/trips/{other['id']}/expenses/import?dry_run=false",
        files={"file": ("gastos.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert resp.json()["imported"] == 2

    imported = client.get(f"/api/v1/trips/{other['id']}/expenses").json()
    assert len(imported) == 2
    by_desc = {e["description"]: e for e in imported}
    assert by_desc["Tren"]["amount_base"] == 30.0
    # el pagador existente se reutiliza (global) y queda asociado al nuevo viaje
    assert by_desc["Cena"]["paid_by_id"] == traveler["id"]
    trip_travelers = client.get(f"/api/v1/trips/{other['id']}").json()["travelers"]
    assert [t["name"] for t in trip_travelers] == ["Romm"]


def test_import_spanish_excel_format(client, trip):
    csv_es = (
        "Fecha;Concepto;Importe;Categoría;Pagador\n"
        "01/04/2026;Cena ramen;1.234,56;Comida;Romm\n"
        "02/04/2026;Metro;;Transporte;Ana\n"
    ).encode("utf-8")

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses/import?dry_run=true",
        files={"file": ("gastos.csv", csv_es, "text/csv")},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert len(result["valid_rows"]) == 1
    row = result["valid_rows"][0]
    assert row["day"] == "2026-04-01"
    assert row["amount"] == 1234.56
    assert row["category"] == "Comida"
    assert row["paid_by"] == "Romm"
    # la fila sin importe da error con su número de fila
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row"] == 3


def test_import_real_excel_format(client, trip):
    """El formato real de la hoja del usuario: fechas largas en español que se heredan,
    importes con €, columna Lugar fusionada en notas y pagador 'Comun'."""
    csv_es = (
        "Descripción\tCantidad\tCategoria\tPagado por\tLugar\tFecha\tNotas\n"
        "Vuelos\t  1.528,00 € \tVuelos\tComun\t\t10 febrero 2026\t\n"
        "Seguro viaje\t  208,00 € \tOtros\tNoelia\t\t10 febrero 2026\t\n"
        "Cena pizza\t  15,00 € \tComida\tComun\t\t\t\n"
        "Hotel Taipei\t  161,00 € \tAlojamiento\tComun\tTaipei\t11 febrero 2026\tSe paga en el alojamiento\n"
        "Comida Taipei\t  25,07 € \tComida\tComun\t\t\t\n"
    ).encode("utf-8")

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses/import?dry_run=false",
        files={"file": ("gastos.csv", csv_es, "text/csv")},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["errors"] == []
    assert result["imported"] == 5

    expenses = client.get(f"/api/v1/trips/{trip['id']}/expenses").json()
    by_desc = {e["description"]: e for e in expenses}

    assert by_desc["Vuelos"]["amount"] == 1528.0
    assert by_desc["Vuelos"]["category"] == "Vuelos"
    assert by_desc["Vuelos"]["day"] == "2026-02-10"
    # la fila sin fecha hereda la de la anterior
    assert by_desc["Cena pizza"]["day"] == "2026-02-10"
    assert by_desc["Comida Taipei"]["day"] == "2026-02-11"
    assert by_desc["Hotel Taipei"]["notes"] == "Se paga en el alojamiento"
    # la columna Lugar crea un sitio real del viaje y lo enlaza al gasto
    places = client.get(f"/api/v1/trips/{trip['id']}/places").json()
    taipei = next(p for p in places if p["name"] == "Taipei")
    assert by_desc["Hotel Taipei"]["place_id"] == taipei["id"]
    # pagadores creados como viajeros globales y asociados al viaje
    travelers = client.get(f"/api/v1/trips/{trip['id']}").json()["travelers"]
    assert sorted(t["name"] for t in travelers) == ["Comun", "Noelia"]


def test_import_creates_unknown_category(client, trip):
    csv_data = "day,description,amount,category\n2026-04-01,Cañas,20,Cerveza\n".encode()
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses/import?dry_run=false",
        files={"file": ("g.csv", csv_data, "text/csv")},
    )
    assert resp.json()["imported"] == 1
    names = [c["name"] for c in client.get("/api/v1/categories?kind=expense").json()]
    assert "Cerveza" in names


def test_import_missing_rate_for_foreign_currency(client, trip):
    csv_data = "day,description,amount,currency\n2026-04-01,Taxi,20,USD\n".encode()
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses/import?dry_run=true",
        files={"file": ("g.csv", csv_data, "text/csv")},
    )
    result = resp.json()
    assert result["valid_rows"] == []
    assert "exchange_rate" in result["errors"][0]["error"]
