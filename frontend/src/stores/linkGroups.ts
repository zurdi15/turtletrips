import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { LinkGroup, LinkGroupInput } from '../api/types'
import { useTripResource } from './tripResource'

export const useLinkGroupsStore = defineStore('linkGroups', () => {
  const base = useTripResource<LinkGroup, LinkGroupInput>({
    listPath: (tripId) => `/trips/${tripId}/link-groups`,
    itemPath: (id) => `/link-groups/${id}`,
  })

  /** Persiste el orden actual (items ya reordenados en local por el drag). */
  function reorder(ids: number[]) {
    return api.post(`/trips/${base.tripId.value}/link-groups/reorder`, { ids })
  }

  return { ...base, reorder }
})
