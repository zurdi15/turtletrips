import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type {
  Expense,
  ExpenseInput,
  ImportResult,
  TripBalances,
  TripSummary,
} from '../api/types'
import { useTripResource } from './tripResource'

export type { ExpenseInput } from '../api/types'

export const useExpensesStore = defineStore('expenses', () => {
  const base = useTripResource<Expense, ExpenseInput>({
    listPath: (tripId) => `/trips/${tripId}/expenses`,
    itemPath: (id) => `/expenses/${id}`,
    insert: 'unshift',
  })
  const summary = ref<TripSummary | null>(null)
  const balances = ref<TripBalances | null>(null)

  async function load(tripId: number) {
    base.loading.value = true
    if (base.tripId.value !== tripId) balances.value = null
    base.tripId.value = tripId
    try {
      ;[base.items.value, summary.value] = await Promise.all([
        api.get<Expense[]>(`/trips/${tripId}/expenses`),
        api.get<TripSummary>(`/trips/${tripId}/summary`),
      ])
    } finally {
      base.loading.value = false
    }
  }

  async function refreshSummary() {
    if (base.tripId.value == null) return
    summary.value = await api.get<TripSummary>(`/trips/${base.tripId.value}/summary`)
    // los saldos solo se refrescan si la pestaña ya los cargó
    if (balances.value != null) await loadBalances()
  }

  async function loadBalances() {
    if (base.tripId.value == null) return
    balances.value = await api.get<TripBalances>(`/trips/${base.tripId.value}/balances`)
  }

  /** Registra un pago entre viajeros; el backend devuelve los saldos ya actualizados. */
  async function settle(transfer: { from_id: number; to_id: number; amount_base: number }) {
    balances.value = await api.post<TripBalances>(
      `/trips/${base.tripId.value}/settlements`,
      transfer,
    )
  }

  async function unsettle(settlementId: number) {
    await api.delete(`/settlements/${settlementId}`)
    await loadBalances()
  }

  async function create(payload: ExpenseInput) {
    const expense = await base.create(payload)
    await refreshSummary()
    return expense
  }

  async function update(id: number, payload: ExpenseInput) {
    const expense = await base.update(id, payload)
    await refreshSummary()
    return expense
  }

  async function remove(id: number) {
    await base.remove(id)
    await refreshSummary()
  }

  async function bulkUpdate(ids: number[], payload: ExpenseInput) {
    await Promise.all(ids.map((id) => api.patch<Expense>(`/expenses/${id}`, payload)))
    if (base.tripId.value != null) await load(base.tripId.value)
    if (balances.value != null) await loadBalances()
  }

  async function bulkRemove(ids: number[]) {
    await Promise.all(ids.map((id) => api.delete(`/expenses/${id}`)))
    if (base.tripId.value != null) await load(base.tripId.value)
    if (balances.value != null) await loadBalances()
  }

  async function importCsv(file: File, dryRun: boolean): Promise<ImportResult> {
    const form = new FormData()
    form.append('file', file)
    const result = await api.upload<ImportResult>(
      `/trips/${base.tripId.value}/expenses/import?dry_run=${dryRun}`,
      form,
    )
    if (!dryRun && base.tripId.value != null) await load(base.tripId.value)
    return result
  }

  function exportUrl(): string {
    return `/api/v1/trips/${base.tripId.value}/expenses/export.csv`
  }

  return {
    ...base,
    summary,
    balances,
    load,
    refreshSummary,
    loadBalances,
    settle,
    unsettle,
    create,
    update,
    remove,
    bulkUpdate,
    bulkRemove,
    importCsv,
    exportUrl,
  }
})
