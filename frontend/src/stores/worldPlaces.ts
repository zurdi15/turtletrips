import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { WorldPlace, WorldPlaceInput } from '../api/types'

export type { WorldPlaceInput } from '../api/types'

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
      // recargar: una ciudad/sitio puede arrastrar su país al diario
      await this.load()
      return place
    },
    async update(id: number, payload: WorldPlaceInput) {
      const place = await api.patch<WorldPlace>(`/world-places/${id}`, payload)
      await this.load()
      return place
    },
    async remove(id: number) {
      await api.delete(`/world-places/${id}`)
      this.items = this.items.filter((p) => p.id !== id)
    },
    async removeMany(ids: number[]) {
      await Promise.all(ids.map((id) => api.delete(`/world-places/${id}`)))
      // recargar: las entradas auto se ocultan en vez de borrarse
      await this.load()
    },
    async uploadPhoto(id: number, file: File): Promise<WorldPlace> {
      const form = new FormData()
      form.append('file', file)
      const place = await api.upload<WorldPlace>(`/world-places/${id}/photo`, form)
      await this.load()
      return place
    },
    async removePhoto(id: number) {
      await api.delete(`/world-places/${id}/photo`)
      await this.load()
    },
  },
})
