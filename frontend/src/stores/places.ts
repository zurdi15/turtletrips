import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Place } from '../api/types'

export interface PlaceInput {
  name?: string
  category?: string
  notes?: string | null
  url?: string | null
  address?: string | null
  lat?: number | null
  lon?: number | null
  visited?: boolean
  priority?: number
}

export const usePlacesStore = defineStore('places', {
  state: () => ({
    items: [] as Place[],
    tripId: null as number | null,
    loading: false,
  }),
  actions: {
    async load(tripId: number) {
      this.loading = true
      this.tripId = tripId
      try {
        this.items = await api.get<Place[]>(`/trips/${tripId}/places`)
      } finally {
        this.loading = false
      }
    },
    async create(payload: PlaceInput) {
      const place = await api.post<Place>(`/trips/${this.tripId}/places`, payload)
      this.items.push(place)
      return place
    },
    async update(id: number, payload: PlaceInput) {
      const place = await api.patch<Place>(`/places/${id}`, payload)
      const idx = this.items.findIndex((p) => p.id === id)
      if (idx >= 0) this.items[idx] = place
      return place
    },
    async toggleVisited(place: Place) {
      // update optimista
      place.visited = !place.visited
      try {
        await api.patch<Place>(`/places/${place.id}`, { visited: place.visited })
      } catch (err) {
        place.visited = !place.visited
        throw err
      }
    },
    async remove(id: number) {
      await api.delete(`/places/${id}`)
      this.items = this.items.filter((p) => p.id !== id)
    },
  },
})
