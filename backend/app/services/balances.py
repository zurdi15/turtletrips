"""Balances entre viajeros: quién pagó, qué le corresponde y cómo saldar.

Todo el cálculo se hace en moneda base sobre amount_base (tasa ya snapshoteada).
Un gasto sin filas en expense_shares se reparte a partes iguales entre los
viajeros ACTUALES del viaje (reparto implícito).
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Expense, Settlement, SplitMode, Traveler, Trip
from ..schemas.expense import ExpenseShareInput
from ..schemas.misc import (
    PaidSettlement,
    SettlementTransfer,
    TravelerBalance,
    TripBalances,
)

CENT = Decimal("0.01")


def split_amount(amount: Decimal, fractions: dict[int, Decimal]) -> dict[int, Decimal]:
    """Reparte `amount` a céntimos según fracciones (no hace falta que sumen 1).

    Método del mayor resto: garantiza sum(resultado) == amount, con empates
    resueltos por traveler_id ascendente (determinista).
    """
    total_fraction = sum(fractions.values(), Decimal(0))
    if not fractions or total_fraction == 0:
        return {}
    cents = int((amount.quantize(CENT) * 100).to_integral_value())
    raw = {tid: Decimal(cents) * f / total_fraction for tid, f in fractions.items()}
    floors = {tid: int(r) for tid, r in raw.items()}
    remainder = cents - sum(floors.values())
    by_largest_remainder = sorted(raw, key=lambda tid: (-(raw[tid] - floors[tid]), tid))
    for tid in by_largest_remainder[:remainder]:
        floors[tid] += 1
    return {tid: Decimal(c) / 100 for tid, c in floors.items()}


def expense_fractions(expense: Expense, trip_traveler_ids: list[int]) -> dict[int, Decimal]:
    """Fracción de participación por viajero para un gasto."""
    if not expense.shares:
        # implícito: todos los viajeros actuales; sin viajeros, solo el pagador (neto 0)
        ids = trip_traveler_ids or ([expense.paid_by_id] if expense.paid_by_id else [])
        return {tid: Decimal(1) for tid in ids}
    if expense.split_mode == SplitMode.equal.value:
        return {s.traveler_id: Decimal(1) for s in expense.shares}
    values = {s.traveler_id: Decimal(str(s.value or 0)) for s in expense.shares}
    if sum(values.values()) == 0:
        return {tid: Decimal(1) for tid in values}
    # normaliza al dividir por la suma en split_amount: robusto ante shares
    # borradas en cascada (el resto absorbe proporcionalmente)
    return values


def suggest_settlements(nets: dict[int, Decimal]) -> list[tuple[int, int, Decimal]]:
    """Liquidación greedy: mayor deudor paga al mayor acreedor. ≤ n-1 transferencias."""
    debtors = sorted(
        ([tid, -net] for tid, net in nets.items() if net < 0),
        key=lambda x: (-x[1], x[0]),
    )
    creditors = sorted(
        ([tid, net] for tid, net in nets.items() if net > 0),
        key=lambda x: (-x[1], x[0]),
    )
    transfers: list[tuple[int, int, Decimal]] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        amount = min(debtors[i][1], creditors[j][1])
        if amount > 0:
            transfers.append((debtors[i][0], creditors[j][0], amount))
        debtors[i][1] -= amount
        creditors[j][1] -= amount
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1
    return transfers


def validate_shares(
    trip: Trip, amount: Decimal, split_mode: str, shares: list[ExpenseShareInput]
) -> None:
    """Valida un reparto; lanza ValueError con mensaje en español."""
    ids = [s.traveler_id for s in shares]
    if len(set(ids)) != len(ids):
        raise ValueError("Hay viajeros repetidos en el reparto")
    member_ids = {t.id for t in trip.travelers}
    if any(tid not in member_ids for tid in ids):
        raise ValueError("Algún viajero del reparto no pertenece a este viaje")
    if split_mode == SplitMode.equal.value:
        return
    if not shares:
        raise ValueError("El reparto personalizado necesita al menos un participante")
    if any(s.value is None for s in shares):
        raise ValueError("Indica el valor de cada participante del reparto")
    total = sum((s.value for s in shares), Decimal(0)).quantize(CENT)
    if split_mode == SplitMode.amount.value and total != amount.quantize(CENT):
        raise ValueError(
            f"Los importes del reparto suman {total} pero el gasto es {amount.quantize(CENT)}"
        )
    if split_mode == SplitMode.percent.value and total != Decimal(100):
        raise ValueError(f"Los porcentajes deben sumar 100 (suman {total})")


def trip_debts_settled(trip: Trip) -> bool:
    """True si hay liquidaciones registradas y con ellas los saldos quedan a cero.

    Trabaja sobre las relaciones del Trip (sin Session explícita) para poder
    usarse como property del modelo; el corte por `settlements` vacío evita
    cargar gastos en los viajes sin liquidaciones (la gran mayoría).
    """
    if not trip.settlements:
        return False
    trip_traveler_ids = [t.id for t in trip.travelers]
    nets: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    for expense in trip.expenses:
        if expense.paid_by_common or expense.paid_by_id is None:
            continue
        amount_base = Decimal(str(expense.amount_base))
        nets[expense.paid_by_id] += amount_base
        for tid, part in split_amount(
            amount_base, expense_fractions(expense, trip_traveler_ids)
        ).items():
            nets[tid] -= part
    for settlement in trip.settlements:
        amount = Decimal(str(settlement.amount_base))
        nets[settlement.from_id] += amount
        nets[settlement.to_id] -= amount
    return all(abs(net) < CENT for net in nets.values())


def trip_balances(db: Session, trip: Trip) -> TripBalances:
    expenses = db.scalars(
        select(Expense)
        .where(Expense.trip_id == trip.id)
        .options(selectinload(Expense.shares))
    ).all()

    trip_traveler_ids = [t.id for t in trip.travelers]
    paid: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    owed: dict[int, Decimal] = defaultdict(lambda: Decimal(0))
    unassigned_count = 0
    unassigned_total = Decimal(0)
    common_count = 0
    common_total = Decimal(0)

    for expense in expenses:
        amount_base = Decimal(str(expense.amount_base))
        if expense.paid_by_common:
            # sale del monedero común: no genera deuda entre viajeros
            common_count += 1
            common_total += amount_base
            continue
        if expense.paid_by_id is None:
            unassigned_count += 1
            unassigned_total += amount_base
            continue
        paid[expense.paid_by_id] += amount_base
        fractions = expense_fractions(expense, trip_traveler_ids)
        for tid, part in split_amount(amount_base, fractions).items():
            owed[tid] += part

    recorded = db.scalars(
        select(Settlement)
        .where(Settlement.trip_id == trip.id)
        .order_by(Settlement.created_at, Settlement.id)
    ).all()

    # universo: viajeros del viaje + pagadores/participantes ya desasociados con saldo
    universe = set(trip_traveler_ids) | set(paid) | set(owed)
    universe |= {s.from_id for s in recorded} | {s.to_id for s in recorded}
    travelers = {
        t.id: t
        for t in db.scalars(select(Traveler).where(Traveler.id.in_(universe)))
    }

    nets = {tid: paid[tid] - owed[tid] for tid in universe if tid in travelers}
    # los pagos registrados saldan deuda: quien pagó sube, quien cobró baja
    for settlement in recorded:
        if settlement.from_id in nets:
            nets[settlement.from_id] += Decimal(str(settlement.amount_base))
        if settlement.to_id in nets:
            nets[settlement.to_id] -= Decimal(str(settlement.amount_base))
    balances = sorted(
        (
            TravelerBalance(
                traveler_id=tid,
                name=travelers[tid].name,
                color=travelers[tid].color,
                paid_base=float(paid[tid]),
                owed_base=float(owed[tid]),
                net_base=float(nets[tid]),
            )
            for tid in nets
        ),
        key=lambda b: b.name.lower(),
    )
    settlements = [
        SettlementTransfer(
            from_id=from_id,
            from_name=travelers[from_id].name,
            to_id=to_id,
            to_name=travelers[to_id].name,
            amount_base=float(amount),
        )
        for from_id, to_id, amount in suggest_settlements(nets)
    ]
    paid_settlements = [
        PaidSettlement(
            id=s.id,
            from_id=s.from_id,
            from_name=travelers[s.from_id].name if s.from_id in travelers else "?",
            to_id=s.to_id,
            to_name=travelers[s.to_id].name if s.to_id in travelers else "?",
            amount_base=float(s.amount_base),
            created_at=s.created_at,
        )
        for s in recorded
    ]
    return TripBalances(
        base_currency=trip.base_currency,
        balances=balances,
        settlements=settlements,
        paid_settlements=paid_settlements,
        debts_settled=bool(recorded) and all(abs(net) < CENT for net in nets.values()),
        unassigned_count=unassigned_count,
        unassigned_total_base=float(unassigned_total),
        common_count=common_count,
        common_total_base=float(common_total),
    )
