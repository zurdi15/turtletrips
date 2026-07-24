import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Booking, BookingInput, Expense } from '../api/types'
import { useTripResource } from './tripResource'

export type { BookingInput } from '../api/types'

export const useBookingsStore = defineStore('bookings', () => {
  const base = useTripResource<Booking, BookingInput>({
    listPath: (tripId) => `/trips/${tripId}/bookings`,
    itemPath: (id) => `/bookings/${id}`,
  })

  async function createExpense(id: number, exchangeRate?: number) {
    const body = exchangeRate !== undefined ? { exchange_rate: exchangeRate } : {}
    return api.post<Expense>(`/bookings/${id}/create-expense`, body)
  }

  return { ...base, createExpense }
})
