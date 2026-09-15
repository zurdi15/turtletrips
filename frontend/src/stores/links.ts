import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { TripLink, TripLinkBucket, TripLinkInput } from '../api/types'
import { useTripResource } from './tripResource'

export const useLinksStore = defineStore('links', () => {
  const base = useTripResource<TripLink, TripLinkInput>({
    listPath: (tripId) => `/trips/${tripId}/links`,
    itemPath: (id) => `/links/${id}`,
  })

  /** Persiste la disposición completa (bloque + orden) tras un drag & drop;
   * el servidor devuelve la lista resultante y se sustituye de golpe. */
  async function reorder(buckets: TripLinkBucket[]) {
    base.items.value = await api.post<TripLink[]>(
      `/trips/${base.tripId.value}/links/reorder`,
      { buckets },
    )
  }

  /** Reintenta la miniatura OG en el servidor; devuelve si la hay. */
  async function refreshImage(id: number): Promise<boolean> {
    const item = await api.post<TripLink>(`/links/${id}/refresh-image`)
    const idx = base.items.value.findIndex((i) => i.id === id)
    if (idx >= 0) base.items.value[idx] = item
    return item.image_url !== null
  }

  /** Foto subida a mano: sustituye a la miniatura (automática o anterior). */
  async function uploadImage(id: number, file: File): Promise<TripLink> {
    const form = new FormData()
    form.append('file', file)
    const item = await api.upload<TripLink>(`/links/${id}/image`, form)
    const idx = base.items.value.findIndex((i) => i.id === id)
    if (idx >= 0) base.items.value[idx] = item
    return item
  }

  async function removeImage(id: number) {
    await api.delete(`/links/${id}/image`)
    const item = base.items.value.find((i) => i.id === id)
    if (item) item.image_url = null
  }

  /** Un bloque borrado deja sus enlaces sin bloque (espejo del SET NULL). */
  function detachGroup(groupId: number) {
    for (const link of base.items.value) {
      if (link.group_id === groupId) link.group_id = null
    }
  }

  return { ...base, reorder, refreshImage, uploadImage, removeImage, detachGroup }
})
