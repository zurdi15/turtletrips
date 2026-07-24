import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Booking, Expense } from '../api/types'

export interface BookingInput {
  type?: string
  title?: string
  provider?: string | null
  confirmation_code?: string | null
  start_dt?: string | null
  end_dt?: string | null
  origin?: string | null
  destination?: string | null
  address?: string | null
  lat?: number | null
  lon?: number | null
  cost_amount?: number | string | null
  cost_currency?: string | null
  notes?: string | null
}

export const useBookingsStore = defineStore('bookings', {
  state: () => ({
    items: [] as Booking[],
    tripId: null as number | null,
    loading: false,
  }),
  actions: {
    async load(tripId: number) {
      this.loading = true
      this.tripId = tripId
      try {
        this.items = await api.get<Booking[]>(`/trips/${tripId}/bookings`)
      } finally {
        this.loading = false
      }
    },
    async create(payload: BookingInput) {
      const booking = await api.post<Booking>(`/trips/${this.tripId}/bookings`, payload)
      this.items.push(booking)
      return booking
    },
    async update(id: number, payload: BookingInput) {
      const booking = await api.patch<Booking>(`/bookings/${id}`, payload)
      const idx = this.items.findIndex((b) => b.id === id)
      if (idx >= 0) this.items[idx] = booking
      return booking
    },
    async remove(id: number) {
      await api.delete(`/bookings/${id}`)
      this.items = this.items.filter((b) => b.id !== id)
    },
    async createExpense(id: number, exchangeRate?: number) {
      const body = exchangeRate !== undefined ? { exchange_rate: exchangeRate } : {}
      return api.post<Expense>(`/bookings/${id}/create-expense`, body)
    },
  },
})
