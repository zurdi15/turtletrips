import { defineStore } from 'pinia'
import type { ChecklistItem, ChecklistInput } from '../api/types'
import { useTripResource } from './tripResource'

export const useChecklistStore = defineStore('checklist', () => {
  return useTripResource<ChecklistItem, ChecklistInput>({
    listPath: (tripId) => `/trips/${tripId}/checklist`,
    itemPath: (id) => `/checklist-items/${id}`,
  })
})
