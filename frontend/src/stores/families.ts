import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Family, FamilyInput } from '../api/types'
import { useGlobalResource } from './globalResource'

export const useFamiliesStore = defineStore('families', () => {
  // sin sort: el orden lo marca el servidor (position, editable con drag & drop)
  const base = useGlobalResource<Family, FamilyInput, FamilyInput>({
    listPath: '/families',
    itemPath: (id) => `/families/${id}`,
  })

  /** Persiste el orden actual (items ya reordenados en local por el drag). */
  function reorder(ids: number[]) {
    return api.post('/families/reorder', { ids })
  }

  return { ...base, reorder }
})
