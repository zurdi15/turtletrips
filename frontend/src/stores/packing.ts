import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type {
  PackingInput,
  PackingItem,
  PackingSelection,
  PackingTemplate,
} from '../api/types'
import { useTripResource } from './tripResource'

export type { PackingInput } from '../api/types'

export const usePackingStore = defineStore('packing', () => {
  const base = useTripResource<PackingItem, PackingInput>({
    listPath: (tripId) => `/trips/${tripId}/packing`,
    itemPath: (id) => `/packing/${id}`,
  })
  const templates = ref<PackingTemplate[]>([])
  const selections = ref<PackingSelection[]>([])

  async function load(tripId: number) {
    base.loading.value = true
    base.tripId.value = tripId
    try {
      ;[base.items.value, templates.value, selections.value] = await Promise.all([
        api.get<PackingItem[]>(`/trips/${tripId}/packing`),
        api.get<PackingTemplate[]>('/packing-templates'),
        api.get<PackingSelection[]>(`/trips/${tripId}/packing/selections`),
      ])
    } finally {
      base.loading.value = false
    }
  }

  async function refreshSelections() {
    if (base.tripId.value == null) return
    selections.value = await api.get<PackingSelection[]>(
      `/trips/${base.tripId.value}/packing/selections`,
    )
  }

  /** Plantilla seleccionada para la maleta de un viajero (null = común) */
  function selectionFor(travelerId: number | null): number | null {
    return selections.value.find((s) => s.traveler_id === travelerId)?.template_id ?? null
  }

  function itemsFor(travelerId: number | null): PackingItem[] {
    return base.items.value.filter((i) => i.traveler_id === travelerId)
  }

  async function toggle(item: PackingItem) {
    // update optimista
    item.checked = !item.checked
    try {
      await api.patch<PackingItem>(`/packing/${item.id}`, { checked: item.checked })
    } catch (err) {
      item.checked = !item.checked
      throw err
    }
  }

  async function saveAsTemplate(name: string, travelerId: number | null) {
    const template = await api.post<PackingTemplate>('/packing-templates', {
      name,
      from_trip_id: base.tripId.value,
      traveler_id: travelerId,
    })
    templates.value.push(template)
    templates.value.sort((a, b) => a.name.localeCompare(b.name, 'es'))
    await refreshSelections()
    return template
  }

  async function applyTemplate(templateId: number, travelerId: number | null) {
    const query = travelerId != null ? `?traveler_id=${travelerId}` : ''
    base.items.value = await api.post<PackingItem[]>(
      `/trips/${base.tripId.value}/packing/apply/${templateId}${query}`,
    )
    await refreshSelections()
  }

  async function syncTemplateFromTrip(templateId: number, travelerId: number | null) {
    const query = travelerId != null ? `?traveler_id=${travelerId}` : ''
    const detail = await api.post<{ id: number; name: string; items: unknown[] }>(
      `/packing-templates/${templateId}/sync-from-trip/${base.tripId.value}${query}`,
    )
    const template = templates.value.find((t) => t.id === templateId)
    if (template) template.item_count = detail.items.length
    await refreshSelections()
    return detail
  }

  return {
    ...base,
    templates,
    selections,
    load,
    refreshSelections,
    selectionFor,
    itemsFor,
    toggle,
    saveAsTemplate,
    applyTemplate,
    syncTemplateFromTrip,
  }
})
