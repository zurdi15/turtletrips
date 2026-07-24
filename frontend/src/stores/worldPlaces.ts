import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { WorldPlace, WorldPlaceKind } from '../api/types'

export interface WorldPlaceInput {
  name?: string
  kind?: WorldPlaceKind
  country_code?: string | null
  lat?: number | null
  lon?: number | null
  note?: string | null
}

export const useWorldPlacesStore = defineStore('worldPlaces', {
  state: () => ({
    items: [] as WorldPlace[],
    loading: false,
  }),
  getters: {
    countries: (state) => state.items.filter((p) => p.kind === 'country'),
    cities: (state) => state.items.filter((p) => p.kind === 'city'),
    pois: (state) => state.items.filter((p) => p.kind === 'place'),
  },
  actions: {
    async load() {
      this.loading = true
      try {
        this.items = await api.get<WorldPlace[]>('/world-places')
      } finally {
        this.loading = false
      }
    },
    async create(payload: WorldPlaceInput) {
      const place = await api.post<WorldPlace>('/world-places', payload)
      this.items.push(place)
      this.items.sort((a, b) => a.name.localeCompare(b.name, 'es'))
      return place
    },
    async update(id: number, payload: WorldPlaceInput) {
      const place = await api.patch<WorldPlace>(`/world-places/${id}`, payload)
      const idx = this.items.findIndex((p) => p.id === id)
      if (idx >= 0) this.items[idx] = place
      return place
    },
    async remove(id: number) {
      await api.delete(`/world-places/${id}`)
      this.items = this.items.filter((p) => p.id !== id)
    },
  },
})
