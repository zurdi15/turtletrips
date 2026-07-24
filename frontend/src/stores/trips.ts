import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Traveler, Trip } from '../api/types'

export interface TripInput {
  name?: string
  countries?: string[]
  start_date?: string | null
  end_date?: string | null
  status_override?: string | null
  base_currency?: string
  budget_amount?: number | string | null
  album_url?: string | null
  notes?: string | null
}

export const useTripsStore = defineStore('trips', {
  state: () => ({
    trips: [] as Trip[],
    current: null as Trip | null,
    loading: false,
  }),
  actions: {
    async loadTrips() {
      this.loading = true
      try {
        this.trips = await api.get<Trip[]>('/trips')
      } finally {
        this.loading = false
      }
    },
    async loadTrip(id: number) {
      this.current = await api.get<Trip>(`/trips/${id}`)
      return this.current
    },
    _replace(trip: Trip) {
      const idx = this.trips.findIndex((t) => t.id === trip.id)
      if (idx >= 0) this.trips[idx] = trip
      if (this.current?.id === trip.id) this.current = trip
    },
    async createTrip(payload: TripInput) {
      const trip = await api.post<Trip>('/trips', payload)
      this.trips.unshift(trip)
      return trip
    },
    async updateTrip(id: number, payload: TripInput) {
      const trip = await api.patch<Trip>(`/trips/${id}`, payload)
      this._replace(trip)
      return trip
    },
    async deleteTrip(id: number) {
      await api.delete(`/trips/${id}`)
      this.trips = this.trips.filter((t) => t.id !== id)
      if (this.current?.id === id) this.current = null
    },
    async addTravelerToTrip(tripId: number, travelerId: number) {
      const travelers = await api.post<Traveler[]>(`/trips/${tripId}/travelers/${travelerId}`)
      if (this.current?.id === tripId) this.current.travelers = travelers
      return travelers
    },
    async removeTravelerFromTrip(tripId: number, travelerId: number) {
      const travelers = await api.delete(`/trips/${tripId}/travelers/${travelerId}`).then(() =>
        api.get<Trip>(`/trips/${tripId}`).then((t) => t.travelers),
      )
      if (this.current?.id === tripId) this.current.travelers = travelers
      return travelers
    },
    async uploadCover(tripId: number, file: File) {
      const form = new FormData()
      form.append('file', file)
      const trip = await api.upload<Trip>(`/trips/${tripId}/cover`, form)
      this._replace(trip)
      return trip
    },
    async deleteCover(tripId: number) {
      const trip = await api.delete(`/trips/${tripId}/cover`).then(() =>
        api.get<Trip>(`/trips/${tripId}`),
      )
      this._replace(trip)
      return trip
    },
  },
})
