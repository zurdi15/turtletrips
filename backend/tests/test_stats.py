def _trip(client, name, start, end, countries):
    return client.post(
        "/api/v1/trips",
        json={"name": name, "start_date": start, "end_date": end, "countries": countries},
    ).json()


def test_yearly_stats(client):
    _trip(client, "Portugal", "2024-05-01", "2024-05-10", ["PT"])
    # cruza Nochevieja: cuenta en ambos años, con los días repartidos
    nye = _trip(client, "Fin de año en Roma", "2024-12-30", "2025-01-02", ["IT"])
    _trip(client, "Vuelta a Lisboa", "2025-08-01", "2025-08-05", ["PT"])

    client.post(
        f"/api/v1/trips/{nye['id']}/expenses",
        json={"day": "2024-12-31", "description": "Cena", "amount": "100"},
    )
    client.post(
        f"/api/v1/trips/{nye['id']}/expenses",
        json={"day": "2025-01-01", "description": "Museo", "amount": "30"},
    )

    years = {y["year"]: y for y in client.get("/api/v1/stats/yearly").json()}
    assert set(years) == {2024, 2025}

    y24, y25 = years[2024], years[2025]
    assert y24["trips"] == 2
    assert y24["days"] == 10 + 2  # Portugal entero + 30-31 de diciembre
    assert y24["countries"] == ["IT", "PT"]
    assert y24["new_countries"] == ["IT", "PT"]
    assert y24["spent"] == [{"currency": "EUR", "amount": 100.0}]

    assert y25["trips"] == 2
    assert y25["days"] == 2 + 5  # 1-2 de enero + Lisboa
    # PT ya estaba estrenado en 2024
    assert y25["new_countries"] == []
    assert y25["spent"] == [{"currency": "EUR", "amount": 30.0}]


def test_yearly_stats_ignores_undated_trips(client):
    _trip(client, "Sin fechas", None, None, ["FR"])
    assert client.get("/api/v1/stats/yearly").json() == []


def test_yearly_stats_includes_retroactive_world_entries(client):
    _trip(client, "Portugal", "2024-05-01", "2024-05-10", ["PT"])
    # país añadido a mano al diario con fecha retroactiva (sin viaje en la app)
    client.post(
        "/api/v1/world-places",
        json={"name": "JP", "kind": "country", "country_code": "JP", "visited_year": 2019},
    )
    # y sin fecha: no puede entrar en ningún año
    client.post(
        "/api/v1/world-places",
        json={"name": "US", "kind": "country", "country_code": "US"},
    )

    years = {y["year"]: y for y in client.get("/api/v1/stats/yearly").json()}
    assert set(years) == {2019, 2024}
    assert years[2019]["countries"] == ["JP"]
    assert years[2019]["new_countries"] == ["JP"]
    assert years[2019]["trips"] == 0
    assert years[2019]["days"] == 0
    assert years[2024]["countries"] == ["PT"]
