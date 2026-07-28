import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Traveler } from '../api/types'
import { useGlobalResource } from './globalResource'

export const useTravelersStore = defineStore('travelers', () => {
  const base = useGlobalResource<
    Traveler,
    { name: string; color?: string | null; family_id?: number | null },
    {
      name?: string
      color?: string | null
      family_id?: number | null
      // encuadre del avatar (0-1); ver utils/imageFocus
      avatar_focus_x?: number
      avatar_focus_y?: number
    }
  >({
    listPath: '/travelers',
    itemPath: (id) => `/travelers/${id}`,
    sort: (a, b) => a.name.localeCompare(b.name, 'es'),
  })

  /** family_id ausente = familia del creador (alta rápida del TripForm). */
  function create(name: string, color?: string | null, familyId?: number | null) {
    return base.create({
      name,
      color,
      ...(familyId !== undefined ? { family_id: familyId } : {}),
    })
  }

  function _replace(item: Traveler) {
    const idx = base.items.value.findIndex((t) => t.id === item.id)
    if (idx >= 0) base.items.value[idx] = item
  }

  async function uploadAvatar(id: number, file: File): Promise<Traveler> {
    const form = new FormData()
    form.append('file', file)
    const item = await api.upload<Traveler>(`/travelers/${id}/avatar`, form)
    _replace(item)
    return item
  }

  async function removeAvatar(id: number): Promise<Traveler> {
    // api.delete ignora el cuerpo de respuesta: se parchea en local
    await api.delete(`/travelers/${id}/avatar`)
    const current = base.items.value.find((t) => t.id === id)
    const updated = { ...(current as Traveler), id, avatar_url: null }
    if (current) _replace(updated)
    return updated
  }

  return { ...base, create, uploadAvatar, removeAvatar }
})
