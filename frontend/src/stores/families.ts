import { defineStore } from 'pinia'
import type { Family, FamilyInput } from '../api/types'
import { useGlobalResource } from './globalResource'

export const useFamiliesStore = defineStore('families', () =>
  useGlobalResource<Family, FamilyInput, FamilyInput>({
    listPath: '/families',
    itemPath: (id) => `/families/${id}`,
    sort: (a, b) => a.name.localeCompare(b.name, 'es'),
  }),
)
