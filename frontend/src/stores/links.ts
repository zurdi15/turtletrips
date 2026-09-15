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

  /** Un bloque borrado deja sus enlaces sin bloque (espejo del SET NULL). */
  function detachGroup(groupId: number) {
    for (const link of base.items.value) {
      if (link.group_id === groupId) link.group_id = null
    }
  }

  return { ...base, reorder, detachGroup }
})
