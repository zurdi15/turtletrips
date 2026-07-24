import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { ItineraryItem } from '../api/types'

export interface ItineraryInput {
  day?: string
  start_time?: string | null
  end_time?: string | null
  order_index?: number
  title?: string
  notes?: string | null
  place_id?: number | null
  booking_id?: number | null
}

export const useItineraryStore = defineStore('itinerary', {
  state: () => ({
    items: [] as ItineraryItem[],
    tripId: null as number | null,
    loading: false,
  }),
  getters: {
    byDay(state): Map<string, ItineraryItem[]> {
      const map = new Map<string, ItineraryItem[]>()
      for (const item of state.items) {
        const list = map.get(item.day) ?? []
        list.push(item)
        map.set(item.day, list)
      }
      for (const list of map.values()) {
        list.sort((a, b) => a.order_index - b.order_index || a.id - b.id)
      }
      return map
    },
  },
  actions: {
    async load(tripId: number) {
      this.loading = true
      this.tripId = tripId
      try {
        this.items = await api.get<ItineraryItem[]>(`/trips/${tripId}/itinerary`)
      } finally {
        this.loading = false
      }
    },
    async create(payload: ItineraryInput) {
      const item = await api.post<ItineraryItem>(`/trips/${this.tripId}/itinerary`, payload)
      this.items.push(item)
      return item
    },
    async update(id: number, payload: ItineraryInput) {
      const item = await api.patch<ItineraryItem>(`/itinerary/${id}`, payload)
      const idx = this.items.findIndex((i) => i.id === id)
      if (idx >= 0) this.items[idx] = item
      return item
    },
    async remove(id: number) {
      await api.delete(`/itinerary/${id}`)
      this.items = this.items.filter((i) => i.id !== id)
    },
    async reorder(entries: { id: number; day: string; order_index: number }[]) {
      // aplicar localmente primero para que el drag no "salte"
      for (const entry of entries) {
        const item = this.items.find((i) => i.id === entry.id)
        if (item) {
          item.day = entry.day
          item.order_index = entry.order_index
        }
      }
      await api.post('/itinerary/reorder', { items: entries })
    },
  },
})
