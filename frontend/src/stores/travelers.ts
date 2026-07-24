import { defineStore } from 'pinia'
import type { Traveler } from '../api/types'
import { useGlobalResource } from './globalResource'

export const useTravelersStore = defineStore('travelers', () => {
  const base = useGlobalResource<
    Traveler,
    { name: string; color?: string | null },
    { name?: string; color?: string | null }
  >({
    listPath: '/travelers',
    itemPath: (id) => `/travelers/${id}`,
    sort: (a, b) => a.name.localeCompare(b.name, 'es'),
  })

  function create(name: string, color?: string | null) {
    return base.create({ name, color })
  }

  return { ...base, create }
})
