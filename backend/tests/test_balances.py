from decimal import Decimal

from app.services.balances import split_amount, suggest_settlements

from conftest import add_traveler


def _expense(client, trip_id, **overrides):
    payload = {"day": "2026-04-01", "description": "Gasto", "amount": "100"}
    payload.update(overrides)
    resp = client.post(f"/api/v1/trips/{trip_id}/expenses", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _balances(client, trip_id):
    resp = client.get(f"/api/v1/trips/{trip_id}/balances")
    assert resp.status_code == 200
    return resp.json()


def _by_name(balances):
    return {b["name"]: b for b in balances["balances"]}


def test_implicit_equal_split(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    add_traveler(client, trip["id"], "Luis")
    _expense(client, trip["id"], amount="100", paid_by_id=ana["id"])

    data = _balances(client, trip["id"])
    by_name = _by_name(data)
    assert by_name["Ana"]["net_base"] == 50.0
    assert by_name["Luis"]["net_base"] == -50.0
    assert data["settlements"] == [
        {
            "from_id": by_name["Luis"]["traveler_id"],
            "from_name": "Luis",
            "to_id": ana["id"],
            "to_name": "Ana",
            "amount_base": 50.0,
        }
    ]


def test_equal_subset_leaves_third_at_zero(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    add_traveler(client, trip["id"], "Marta")
    _expense(
        client,
        trip["id"],
        amount="80",
        paid_by_id=ana["id"],
        split_mode="equal",
        shares=[{"traveler_id": ana["id"]}, {"traveler_id": luis["id"]}],
    )

    by_name = _by_name(_balances(client, trip["id"]))
    assert by_name["Ana"]["net_base"] == 40.0
    assert by_name["Luis"]["net_base"] == -40.0
    assert by_name["Marta"]["net_base"] == 0.0


def test_amount_split_valid_and_invalid(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    _expense(
        client,
        trip["id"],
        amount="100",
        paid_by_id=ana["id"],
        split_mode="amount",
        shares=[
            {"traveler_id": ana["id"], "value": "30"},
            {"traveler_id": luis["id"], "value": "70"},
        ],
    )
    by_name = _by_name(_balances(client, trip["id"]))
    assert by_name["Ana"]["owed_base"] == 30.0
    assert by_name["Luis"]["owed_base"] == 70.0

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2026-04-01",
            "description": "Mal",
            "amount": "100",
            "split_mode": "amount",
            "shares": [{"traveler_id": ana["id"], "value": "30"}],
        },
    )
    assert resp.status_code == 400
    assert "suman" in resp.json()["detail"]


def test_percent_split_valid_and_invalid(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    _expense(
        client,
        trip["id"],
        amount="200",
        paid_by_id=ana["id"],
        split_mode="percent",
        shares=[
            {"traveler_id": ana["id"], "value": "25"},
            {"traveler_id": luis["id"], "value": "75"},
        ],
    )
    by_name = _by_name(_balances(client, trip["id"]))
    assert by_name["Luis"]["owed_base"] == 150.0

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2026-04-01",
            "description": "Mal",
            "amount": "100",
            "split_mode": "percent",
            "shares": [{"traveler_id": ana["id"], "value": "80"}],
        },
    )
    assert resp.status_code == 400
    assert "100" in resp.json()["detail"]


def test_rounding_sums_exactly(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    add_traveler(client, trip["id"], "Luis")
    add_traveler(client, trip["id"], "Marta")
    _expense(client, trip["id"], amount="100", paid_by_id=ana["id"])

    data = _balances(client, trip["id"])
    owed = sorted(b["owed_base"] for b in data["balances"])
    assert owed == [33.33, 33.33, 33.34]
    assert round(sum(b["net_base"] for b in data["balances"]), 2) == 0.0


def test_multicurrency_uses_amount_base(client, trip, db_session):
    from test_expenses import _seed_rate

    ana = add_traveler(client, trip["id"], "Ana")
    add_traveler(client, trip["id"], "Luis")
    _seed_rate(db_session, "JPY", "EUR", "2026-04-02", "0.006")
    _expense(
        client,
        trip["id"],
        day="2026-04-02",
        amount="3000",
        currency="JPY",
        paid_by_id=ana["id"],
    )

    by_name = _by_name(_balances(client, trip["id"]))
    # 3000 JPY * 0.006 = 18 EUR repartidos entre dos
    assert by_name["Ana"]["paid_base"] == 18.0
    assert by_name["Ana"]["net_base"] == 9.0


def test_unassigned_expenses_reported_not_counted(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    _expense(client, trip["id"], amount="50", paid_by_id=ana["id"])
    _expense(client, trip["id"], amount="30")  # sin pagador

    data = _balances(client, trip["id"])
    assert data["unassigned_count"] == 1
    assert data["unassigned_total_base"] == 30.0
    assert _by_name(data)["Ana"]["paid_base"] == 50.0


def test_greedy_settlements_max_n_minus_one(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    marta = add_traveler(client, trip["id"], "Marta")
    add_traveler(client, trip["id"], "Pau")
    _expense(client, trip["id"], amount="100", paid_by_id=ana["id"])
    _expense(client, trip["id"], amount="60", paid_by_id=luis["id"])
    _expense(client, trip["id"], amount="20", paid_by_id=marta["id"])

    data = _balances(client, trip["id"])
    assert len(data["settlements"]) <= 3
    # las transferencias cuadran los netos
    net = {b["traveler_id"]: b["net_base"] for b in data["balances"]}
    for t in data["settlements"]:
        net[t["from_id"]] = round(net[t["from_id"]] + t["amount_base"], 2)
        net[t["to_id"]] = round(net[t["to_id"]] - t["amount_base"], 2)
    assert all(v == 0 for v in net.values())


def test_delete_traveler_cascades_shares(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    expense = _expense(
        client,
        trip["id"],
        amount="100",
        paid_by_id=ana["id"],
        split_mode="amount",
        shares=[
            {"traveler_id": ana["id"], "value": "40"},
            {"traveler_id": luis["id"], "value": "60"},
        ],
    )
    assert client.delete(f"/api/v1/travelers/{luis['id']}").status_code == 204

    expenses = client.get(f"/api/v1/trips/{trip['id']}/expenses").json()
    shares = next(e for e in expenses if e["id"] == expense["id"])["shares"]
    assert [s["traveler_id"] for s in shares] == [ana["id"]]
    # el reparto restante absorbe el total (normalización por suma)
    by_name = _by_name(_balances(client, trip["id"]))
    assert by_name["Ana"]["owed_base"] == 100.0


def test_disassociated_traveler_with_shares_stays_in_balances(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    _expense(
        client,
        trip["id"],
        amount="100",
        paid_by_id=ana["id"],
        split_mode="equal",
        shares=[{"traveler_id": ana["id"]}, {"traveler_id": luis["id"]}],
    )
    _expense(client, trip["id"], amount="40", paid_by_id=ana["id"])  # implícito

    # desasociar del viaje no borra el viajero global ni sus shares
    client.delete(f"/api/v1/trips/{trip['id']}/travelers/{luis['id']}")
    data = _balances(client, trip["id"])
    by_name = _by_name(data)
    # sigue debiendo su mitad del gasto con reparto explícito…
    assert by_name["Luis"]["owed_base"] == 50.0
    # …pero el implícito ya solo cuenta a Ana
    assert by_name["Ana"]["owed_base"] == 50.0 + 40.0


def test_patch_amount_rescales_amount_shares(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    expense = _expense(
        client,
        trip["id"],
        amount="100",
        paid_by_id=ana["id"],
        split_mode="amount",
        shares=[
            {"traveler_id": ana["id"], "value": "25"},
            {"traveler_id": luis["id"], "value": "75"},
        ],
    )
    resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={"amount": "200"})
    assert resp.status_code == 200
    values = {s["traveler_id"]: s["value"] for s in resp.json()["shares"]}
    assert values == {ana["id"]: 50.0, luis["id"]: 150.0}


def test_patch_shares_reset_to_implicit(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    expense = _expense(
        client,
        trip["id"],
        amount="100",
        paid_by_id=ana["id"],
        split_mode="amount",
        shares=[
            {"traveler_id": ana["id"], "value": "10"},
            {"traveler_id": luis["id"], "value": "90"},
        ],
    )
    resp = client.patch(
        f"/api/v1/expenses/{expense['id']}", json={"split_mode": "equal", "shares": []}
    )
    assert resp.status_code == 200
    assert resp.json()["shares"] == []
    assert resp.json()["split_mode"] == "equal"
    by_name = _by_name(_balances(client, trip["id"]))
    assert by_name["Luis"]["owed_base"] == 50.0


def test_share_for_foreign_traveler_rejected(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    outsider = client.post("/api/v1/travelers", json={"name": "Extraño"}).json()
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/expenses",
        json={
            "day": "2026-04-01",
            "description": "Mal",
            "amount": "100",
            "paid_by_id": ana["id"],
            "split_mode": "equal",
            "shares": [{"traveler_id": outsider["id"]}],
        },
    )
    assert resp.status_code == 400
    assert "no pertenece" in resp.json()["detail"]


def test_common_expense_excluded_from_balances(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    add_traveler(client, trip["id"], "Luis")
    _expense(client, trip["id"], amount="100", paid_by_id=ana["id"])
    common = _expense(client, trip["id"], amount="60", paid_by_common=True)
    assert common["paid_by_common"] is True
    assert common["paid_by_id"] is None

    data = _balances(client, trip["id"])
    # el gasto común no genera deuda: los saldos solo reflejan el gasto de Ana
    by_name = _by_name(data)
    assert by_name["Ana"]["net_base"] == 50.0
    assert by_name["Luis"]["net_base"] == -50.0
    assert data["common_count"] == 1
    assert data["common_total_base"] == 60.0
    assert data["unassigned_count"] == 0


def test_common_and_payer_are_mutually_exclusive(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    # crear con ambos: gana el fondo común
    expense = _expense(
        client, trip["id"], amount="10", paid_by_id=ana["id"], paid_by_common=True
    )
    assert expense["paid_by_id"] is None
    assert expense["paid_by_common"] is True

    # asignar pagador desmarca el fondo común
    resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={"paid_by_id": ana["id"]})
    assert resp.json()["paid_by_common"] is False
    assert resp.json()["paid_by_id"] == ana["id"]

    # marcar fondo común suelta al pagador
    resp = client.patch(f"/api/v1/expenses/{expense['id']}", json={"paid_by_common": True})
    assert resp.json()["paid_by_common"] is True
    assert resp.json()["paid_by_id"] is None


def test_common_expense_counts_in_summary_total(client, trip):
    add_traveler(client, trip["id"], "Ana")
    _expense(client, trip["id"], amount="40", paid_by_common=True)
    summary = client.get(f"/api/v1/trips/{trip['id']}/summary").json()
    assert summary["total_base"] == 40.0


def test_split_amount_unit():
    result = split_amount(Decimal("100.00"), {1: Decimal(1), 2: Decimal(1), 3: Decimal(1)})
    assert sum(result.values()) == Decimal("100.00")
    assert result[1] == Decimal("33.34")  # el resto va al id más bajo
    assert result[2] == result[3] == Decimal("33.33")
    assert split_amount(Decimal("10.00"), {}) == {}


def test_suggest_settlements_unit():
    nets = {1: Decimal(60), 2: Decimal(-40), 3: Decimal(-20)}
    transfers = suggest_settlements(nets)
    assert transfers == [(2, 1, Decimal(40)), (3, 1, Decimal(20))]
    assert suggest_settlements({1: Decimal(0)}) == []


def test_settlement_clears_debts_and_pill(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    _expense(client, trip["id"], amount="100", paid_by_id=ana["id"])

    data = _balances(client, trip["id"])
    assert len(data["settlements"]) == 1
    assert data["debts_settled"] is False
    transfer = data["settlements"][0]

    # registrar el pago sugerido: los saldos quedan a cero
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/settlements",
        json={
            "from_id": transfer["from_id"],
            "to_id": transfer["to_id"],
            "amount_base": str(transfer["amount_base"]),
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["settlements"] == []
    assert data["debts_settled"] is True
    assert len(data["paid_settlements"]) == 1
    assert data["paid_settlements"][0]["from_name"] == "Luis"
    by_name = _by_name(data)
    assert by_name["Ana"]["net_base"] == 0.0
    assert by_name["Luis"]["net_base"] == 0.0

    # la pill del viaje refleja las deudas saldadas
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["debts_settled"] is True

    # deshacer el pago: vuelven la deuda y la sugerencia
    settlement_id = data["paid_settlements"][0]["id"]
    assert client.delete(f"/api/v1/settlements/{settlement_id}").status_code == 204
    data = _balances(client, trip["id"])
    assert len(data["settlements"]) == 1
    assert data["debts_settled"] is False
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["debts_settled"] is False


def test_settlement_validation(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    resp = client.post(
        f"/api/v1/trips/{trip['id']}/settlements",
        json={"from_id": ana["id"], "to_id": ana["id"], "amount_base": "10"},
    )
    assert resp.status_code == 400

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/settlements",
        json={"from_id": ana["id"], "to_id": 9999, "amount_base": "10"},
    )
    assert resp.status_code == 404


def test_partial_settlement_reduces_suggestion(client, trip):
    ana = add_traveler(client, trip["id"], "Ana")
    luis = add_traveler(client, trip["id"], "Luis")
    _expense(client, trip["id"], amount="100", paid_by_id=ana["id"])

    resp = client.post(
        f"/api/v1/trips/{trip['id']}/settlements",
        json={"from_id": luis["id"], "to_id": ana["id"], "amount_base": "20"},
    )
    data = resp.json()
    # pagó 20 de los 50: queda una sugerencia de 30 y las deudas NO están saldadas
    assert data["settlements"][0]["amount_base"] == 30.0
    assert data["debts_settled"] is False


def test_trip_without_settlements_not_marked_settled(client, trip):
    add_traveler(client, trip["id"], "Ana")
    # sin gastos ni liquidaciones: la pill no debe salir aunque los saldos sean cero
    assert client.get(f"/api/v1/trips/{trip['id']}").json()["debts_settled"] is False
