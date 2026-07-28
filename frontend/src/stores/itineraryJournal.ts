import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'
import type { DayJournal } from '../api/types'

// Diario + postal por día. A diferencia del resto de recursos, se indexa por
// `day` (string) y no por id numérico, así que no usa tripResource.
export const useItineraryJournalStore = defineStore('itineraryJournal', () => {
  const items = ref<DayJournal[]>([])
  const tripId = ref<number | null>(null)
  const loading = ref(false)

  const byDay = computed(() => new Map(items.value.map((j) => [j.day, j])))

  function _upsert(entry: DayJournal) {
    const idx = items.value.findIndex((j) => j.day === entry.day)
    if (idx >= 0) items.value[idx] = entry
    else items.value.push(entry)
  }

  async function load(id: number) {
    tripId.value = id
    loading.value = true
    try {
      items.value = await api.get<DayJournal[]>(`/trips/${id}/journal`)
    } finally {
      loading.value = false
    }
  }

  async function saveText(day: string, text: string) {
    const entry = await api.put<DayJournal>(`/trips/${tripId.value}/journal/${day}`, {
      text: text || null,
    })
    _upsert(entry)
    return entry
  }

  /**
   * Encuadre de la postal. Va con el texto ACTUAL a cuestas a propósito: el
   * PUT del diario reescribe la fila entera, así que mandar solo el encuadre
   * borraría lo escrito ese día.
   */
  async function saveFocus(day: string, focusX: number, focusY: number) {
    const entry = await api.put<DayJournal>(`/trips/${tripId.value}/journal/${day}`, {
      text: byDay.value.get(day)?.text ?? null,
      photo_focus_x: focusX,
      photo_focus_y: focusY,
    })
    _upsert(entry)
    return entry
  }

  async function uploadPhoto(day: string, file: File) {
    const form = new FormData()
    form.append('file', file)
    const entry = await api.upload<DayJournal>(
      `/trips/${tripId.value}/journal/${day}/photo`,
      form,
    )
    _upsert(entry)
    return entry
  }

  async function deletePhoto(day: string) {
    await api.delete(`/trips/${tripId.value}/journal/${day}/photo`)
    // el endpoint devuelve la fila actualizada, pero api.delete ignora el cuerpo:
    // parcheamos el estado local quitando solo la foto
    const existing = byDay.value.get(day)
    if (existing) _upsert({ ...existing, photo_url: null })
  }

  return { items, tripId, loading, byDay, load, saveText, saveFocus, uploadPhoto, deletePhoto }
})
