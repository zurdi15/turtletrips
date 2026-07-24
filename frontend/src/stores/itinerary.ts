import { computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { ItineraryInput, ItineraryItem } from '../api/types'
import { useTripResource } from './tripResource'

export type { ItineraryInput } from '../api/types'

export const useItineraryStore = defineStore('itinerary', () => {
  const base = useTripResource<ItineraryItem, ItineraryInput>({
    listPath: (tripId) => `/trips/${tripId}/itinerary`,
    itemPath: (id) => `/itinerary/${id}`,
  })

  const byDay = computed(() => {
    const map = new Map<string, ItineraryItem[]>()
    for (const item of base.items.value) {
      const list = map.get(item.day) ?? []
      list.push(item)
      map.set(item.day, list)
    }
    for (const list of map.values()) {
      list.sort((a, b) => a.order_index - b.order_index || a.id - b.id)
    }
    return map
  })

  async function reorder(entries: { id: number; day: string; order_index: number }[]) {
    // aplicar localmente primero para que el drag no "salte"
    for (const entry of entries) {
      const item = base.items.value.find((i) => i.id === entry.id)
      if (item) {
        item.day = entry.day
        item.order_index = entry.order_index
      }
    }
    await api.post('/itinerary/reorder', { items: entries })
  }

  return { ...base, byDay, reorder }
})
