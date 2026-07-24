import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { PackingItem, PackingSelection, PackingTemplate } from '../api/types'

export interface PackingInput {
  name?: string
  category?: string
  url?: string | null
  checked?: boolean
  traveler_id?: number | null
}

export const usePackingStore = defineStore('packing', {
  state: () => ({
    items: [] as PackingItem[],
    templates: [] as PackingTemplate[],
    selections: [] as PackingSelection[],
    tripId: null as number | null,
    loading: false,
  }),
  getters: {
    /** Plantilla seleccionada para la maleta de un viajero (null = común) */
    selectionFor(state) {
      return (travelerId: number | null): number | null =>
        state.selections.find((s) => s.traveler_id === travelerId)?.template_id ?? null
    },
    itemsFor(state) {
      return (travelerId: number | null): PackingItem[] =>
        state.items.filter((i) => i.traveler_id === travelerId)
    },
  },
  actions: {
    async load(tripId: number) {
      this.loading = true
      this.tripId = tripId
      try {
        ;[this.items, this.templates, this.selections] = await Promise.all([
          api.get<PackingItem[]>(`/trips/${tripId}/packing`),
          api.get<PackingTemplate[]>('/packing-templates'),
          api.get<PackingSelection[]>(`/trips/${tripId}/packing/selections`),
        ])
      } finally {
        this.loading = false
      }
    },
    async refreshSelections() {
      if (this.tripId == null) return
      this.selections = await api.get<PackingSelection[]>(
        `/trips/${this.tripId}/packing/selections`,
      )
    },
    async create(payload: PackingInput) {
      const item = await api.post<PackingItem>(`/trips/${this.tripId}/packing`, payload)
      this.items.push(item)
      return item
    },
    async update(id: number, payload: PackingInput) {
      const item = await api.patch<PackingItem>(`/packing/${id}`, payload)
      const idx = this.items.findIndex((i) => i.id === id)
      if (idx >= 0) this.items[idx] = item
      return item
    },
    async toggle(item: PackingItem) {
      // update optimista
      item.checked = !item.checked
      try {
        await api.patch<PackingItem>(`/packing/${item.id}`, { checked: item.checked })
      } catch (err) {
        item.checked = !item.checked
        throw err
      }
    },
    async remove(id: number) {
      await api.delete(`/packing/${id}`)
      this.items = this.items.filter((i) => i.id !== id)
    },
    async saveAsTemplate(name: string, travelerId: number | null) {
      const template = await api.post<PackingTemplate>('/packing-templates', {
        name,
        from_trip_id: this.tripId,
        traveler_id: travelerId,
      })
      this.templates.push(template)
      this.templates.sort((a, b) => a.name.localeCompare(b.name, 'es'))
      await this.refreshSelections()
      return template
    },
    async applyTemplate(templateId: number, travelerId: number | null) {
      const query = travelerId != null ? `?traveler_id=${travelerId}` : ''
      this.items = await api.post<PackingItem[]>(
        `/trips/${this.tripId}/packing/apply/${templateId}${query}`,
      )
      await this.refreshSelections()
    },
    async syncTemplateFromTrip(templateId: number, travelerId: number | null) {
      const query = travelerId != null ? `?traveler_id=${travelerId}` : ''
      const detail = await api.post<{ id: number; name: string; items: unknown[] }>(
        `/packing-templates/${templateId}/sync-from-trip/${this.tripId}${query}`,
      )
      const template = this.templates.find((t) => t.id === templateId)
      if (template) template.item_count = detail.items.length
      await this.refreshSelections()
      return detail
    },
  },
})
