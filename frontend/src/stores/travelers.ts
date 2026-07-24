import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Traveler } from '../api/types'

export const useTravelersStore = defineStore('travelers', {
  state: () => ({
    items: [] as Traveler[],
    loaded: false,
  }),
  actions: {
    async load(force = false) {
      if (this.loaded && !force) return
      this.items = await api.get<Traveler[]>('/travelers')
      this.loaded = true
    },
    async create(name: string, color?: string | null) {
      const traveler = await api.post<Traveler>('/travelers', { name, color })
      if (!this.items.some((t) => t.id === traveler.id)) {
        this.items.push(traveler)
        this.items.sort((a, b) => a.name.localeCompare(b.name, 'es'))
      }
      return traveler
    },
    async update(id: number, payload: { name?: string; color?: string | null }) {
      const traveler = await api.patch<Traveler>(`/travelers/${id}`, payload)
      const idx = this.items.findIndex((t) => t.id === id)
      if (idx >= 0) this.items[idx] = traveler
      return traveler
    },
    async remove(id: number) {
      await api.delete(`/travelers/${id}`)
      this.items = this.items.filter((t) => t.id !== id)
    },
  },
})
