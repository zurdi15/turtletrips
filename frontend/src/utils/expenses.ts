import type { Expense } from '../api/types'
import { toIsoDate } from '../composables/useMoney'
import { daysBetween } from './dates'

export interface ExpenseFilterState {
  searchText: string
  category: string // 'all' o nombre de categoría
  excludedCategories: string[]
  payer: number | 'all' | 'none' | 'common'
  place: number | 'all' | 'none'
  dateFrom: Date | null
  dateTo: Date | null
}

export function emptyFilters(): ExpenseFilterState {
  return {
    searchText: '',
    category: 'all',
    excludedCategories: [],
    payer: 'all',
    place: 'all',
    dateFrom: null,
    dateTo: null,
  }
}

export function countActiveFilters(f: ExpenseFilterState): number {
  return (
    (f.searchText.trim() ? 1 : 0) +
    (f.category !== 'all' ? 1 : 0) +
    (f.excludedCategories.length ? 1 : 0) +
    (f.payer !== 'all' ? 1 : 0) +
    (f.place !== 'all' ? 1 : 0) +
    (f.dateFrom ? 1 : 0) +
    (f.dateTo ? 1 : 0)
  )
}

export function filterExpenses(
  items: Expense[],
  f: ExpenseFilterState,
  placeName: (e: Expense) => string,
): Expense[] {
  return items.filter((e) => {
    if (f.category !== 'all' && e.category !== f.category) return false
    if (f.excludedCategories.includes(e.category)) return false
    if (f.payer === 'common' && !e.paid_by_common) return false
    if (f.payer === 'none' && (e.paid_by_id != null || e.paid_by_common)) return false
    if (
      f.payer !== 'all' &&
      f.payer !== 'none' &&
      f.payer !== 'common' &&
      e.paid_by_id !== f.payer
    )
      return false
    if (f.place === 'none' && e.place_id != null) return false
    if (f.place !== 'all' && f.place !== 'none' && e.place_id !== f.place) return false
    if (f.dateFrom && e.day < toIsoDate(f.dateFrom)) return false
    if (f.dateTo && e.day > toIsoDate(f.dateTo)) return false
    if (f.searchText) {
      const q = f.searchText.toLowerCase()
      if (
        !e.description.toLowerCase().includes(q) &&
        !(e.notes ?? '').toLowerCase().includes(q) &&
        !e.category.toLowerCase().includes(q) &&
        !placeName(e).toLowerCase().includes(q)
      )
        return false
    }
    return true
  })
}

export interface ExpenseStats {
  total: number
  count: number
  travelers: number
  days: number | null
  perPerson: number | null
  perDay: number | null
  perDayPerson: number | null
}

/** Días del viaje si tiene fechas; si no, días distintos con gasto (o null). */
export function tripDayCount(
  startDate: string | null,
  endDate: string | null,
  filtered: Expense[],
): number | null {
  if (startDate && endDate) {
    return daysBetween(startDate, endDate) + 1
  }
  const days = new Set(filtered.map((e) => e.day))
  return days.size || null
}

/** % de presupuesto consumido (capado a 100); null sin presupuesto definido. */
export function budgetPercent(
  summary: { total_base: number; budget_amount: number | null } | null | undefined,
): number | null {
  if (!summary?.budget_amount) return null
  return Math.min(100, Math.round((summary.total_base / summary.budget_amount) * 100))
}

/** Gasto ya generado desde cada reserva (booking_id → expense_id). */
export function expenseIdByBooking(expenses: Expense[]): Map<number, number> {
  const map = new Map<number, number>()
  for (const e of expenses) if (e.booking_id != null) map.set(e.booking_id, e.id)
  return map
}

export function computeStats(
  filtered: Expense[],
  travelers: number,
  days: number | null,
): ExpenseStats {
  const total = filtered.reduce((acc, e) => acc + e.amount_base, 0)
  return {
    total,
    count: filtered.length,
    travelers,
    days,
    perPerson: travelers ? total / travelers : null,
    perDay: days ? total / days : null,
    perDayPerson: travelers && days ? total / days / travelers : null,
  }
}

/** Importes en moneda original distinta de la base: [moneda, suma]. */
export function currencyBreakdown(filtered: Expense[], baseCurrency: string): [string, number][] {
  const map = new Map<string, number>()
  for (const e of filtered) {
    if (e.currency !== baseCurrency) {
      map.set(e.currency, (map.get(e.currency) ?? 0) + e.amount)
    }
  }
  return [...map.entries()]
}

export interface SeriesPoint {
  label: string
  value: number
}

export function aggregate(
  items: Expense[],
  keyOf: (e: Expense) => string,
): SeriesPoint[] {
  const map = new Map<string, number>()
  for (const e of items) {
    const key = keyOf(e)
    map.set(key, (map.get(key) ?? 0) + e.amount_base)
  }
  return [...map.entries()].map(([label, value]) => ({ label, value }))
}

export function cumulative(series: SeriesPoint[]): SeriesPoint[] {
  let acc = 0
  return series.map((d) => ({ label: d.label, value: (acc += d.value) }))
}

// ---- tabla con agrupación ----

export type ExpenseGroupBy = 'none' | 'day' | 'category' | 'payer_name' | 'place_name'

export interface ExpenseRow extends Expense {
  payer_name: string
  place_name: string
}

export function buildRows(
  filtered: Expense[],
  payerName: (e: Expense) => string,
  placeName: (e: Expense) => string,
): ExpenseRow[] {
  return filtered.map((e) => ({ ...e, payer_name: payerName(e), place_name: placeName(e) }))
}

export function sortRows(rows: ExpenseRow[], groupBy: ExpenseGroupBy): ExpenseRow[] {
  const byDayDesc = (a: ExpenseRow, b: ExpenseRow) => b.day.localeCompare(a.day) || b.id - a.id
  const sorted = [...rows]
  if (groupBy === 'category')
    return sorted.sort((a, b) => a.category.localeCompare(b.category, 'es') || byDayDesc(a, b))
  if (groupBy === 'payer_name') {
    // fondo común primero, viajeros por orden alfabético, "sin asignar" al final
    const rank = (r: ExpenseRow) => (r.paid_by_common ? 0 : r.paid_by_id != null ? 1 : 2)
    return sorted.sort(
      (a, b) =>
        rank(a) - rank(b) || a.payer_name.localeCompare(b.payer_name, 'es') || byDayDesc(a, b),
    )
  }
  if (groupBy === 'place_name')
    return sorted.sort((a, b) => a.place_name.localeCompare(b.place_name, 'es') || byDayDesc(a, b))
  return sorted.sort(byDayDesc)
}

/** clave de agrupación de una fila (día, categoría, pagador o sitio) */
export function rowGroupKey(row: ExpenseRow, groupBy: ExpenseGroupBy): string {
  return String(row[groupBy as keyof ExpenseRow])
}

/** filas que comparten grupo con `row` */
export function rowsInGroup(
  rows: ExpenseRow[],
  row: ExpenseRow,
  groupBy: ExpenseGroupBy,
): ExpenseRow[] {
  const key = rowGroupKey(row, groupBy)
  return rows.filter((r) => rowGroupKey(r, groupBy) === key)
}

/** true si TODAS las filas del grupo de `row` están en la selección */
export function isGroupSelected(
  rows: ExpenseRow[],
  selected: ExpenseRow[],
  row: ExpenseRow,
  groupBy: ExpenseGroupBy,
): boolean {
  const group = rowsInGroup(rows, row, groupBy)
  return group.length > 0 && group.every((r) => selected.some((s) => s.id === r.id))
}

/** alterna el grupo entero: lo quita si estaba completo, lo completa si no */
export function toggleGroupSelection(
  rows: ExpenseRow[],
  selected: ExpenseRow[],
  row: ExpenseRow,
  groupBy: ExpenseGroupBy,
): ExpenseRow[] {
  const group = rowsInGroup(rows, row, groupBy)
  if (isGroupSelected(rows, selected, row, groupBy)) {
    const ids = new Set(group.map((r) => r.id))
    return selected.filter((s) => !ids.has(s.id))
  }
  const have = new Set(selected.map((s) => s.id))
  return [...selected, ...group.filter((r) => !have.has(r.id))]
}

/** alterna una fila suelta en la selección */
export function toggleRowSelection(selected: ExpenseRow[], row: ExpenseRow): ExpenseRow[] {
  return selected.some((s) => s.id === row.id)
    ? selected.filter((s) => s.id !== row.id)
    : [...selected, row]
}

export function groupTotals(
  rows: ExpenseRow[],
  groupBy: ExpenseGroupBy,
): Map<string, { total: number; count: number }> {
  const map = new Map<string, { total: number; count: number }>()
  if (groupBy === 'none') return map
  for (const row of rows) {
    const key = String(row[groupBy as keyof ExpenseRow])
    const entry = map.get(key) ?? { total: 0, count: 0 }
    entry.total += row.amount_base
    entry.count += 1
    map.set(key, entry)
  }
  return map
}
