import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Expense, ImportResult, TripSummary } from '../api/types'

export interface ExpenseInput {
  day?: string
  category?: string
  description?: string
  amount?: number | string
  currency?: string
  exchange_rate?: number | string | null
  paid_by_id?: number | null
  booking_id?: number | null
  place_id?: number | null
  notes?: string | null
}

export const useExpensesStore = defineStore('expenses', {
  state: () => ({
    items: [] as Expense[],
    summary: null as TripSummary | null,
    tripId: null as number | null,
    loading: false,
  }),
  actions: {
    async load(tripId: number) {
      this.loading = true
      this.tripId = tripId
      try {
        ;[this.items, this.summary] = await Promise.all([
          api.get<Expense[]>(`/trips/${tripId}/expenses`),
          api.get<TripSummary>(`/trips/${tripId}/summary`),
        ])
      } finally {
        this.loading = false
      }
    },
    async refreshSummary() {
      if (this.tripId == null) return
      this.summary = await api.get<TripSummary>(`/trips/${this.tripId}/summary`)
    },
    async create(payload: ExpenseInput) {
      const expense = await api.post<Expense>(`/trips/${this.tripId}/expenses`, payload)
      this.items.unshift(expense)
      await this.refreshSummary()
      return expense
    },
    async update(id: number, payload: ExpenseInput) {
      const expense = await api.patch<Expense>(`/expenses/${id}`, payload)
      const idx = this.items.findIndex((e) => e.id === id)
      if (idx >= 0) this.items[idx] = expense
      await this.refreshSummary()
      return expense
    },
    async remove(id: number) {
      await api.delete(`/expenses/${id}`)
      this.items = this.items.filter((e) => e.id !== id)
      await this.refreshSummary()
    },
    async bulkUpdate(ids: number[], payload: ExpenseInput) {
      await Promise.all(ids.map((id) => api.patch<Expense>(`/expenses/${id}`, payload)))
      if (this.tripId != null) await this.load(this.tripId)
    },
    async bulkRemove(ids: number[]) {
      await Promise.all(ids.map((id) => api.delete(`/expenses/${id}`)))
      if (this.tripId != null) await this.load(this.tripId)
    },
    async importCsv(file: File, dryRun: boolean): Promise<ImportResult> {
      const form = new FormData()
      form.append('file', file)
      const result = await api.upload<ImportResult>(
        `/trips/${this.tripId}/expenses/import?dry_run=${dryRun}`,
        form,
      )
      if (!dryRun && this.tripId != null) await this.load(this.tripId)
      return result
    },
    exportUrl(): string {
      return `/api/v1/trips/${this.tripId}/expenses/export.csv`
    },
  },
})
