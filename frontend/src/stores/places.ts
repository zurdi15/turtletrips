import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { Place, PlaceInput } from '../api/types'
import { useTripResource } from './tripResource'

export type { PlaceInput } from '../api/types'

export const usePlacesStore = defineStore('places', () => {
  const base = useTripResource<Place, PlaceInput>({
    listPath: (tripId) => `/trips/${tripId}/places`,
    itemPath: (id) => `/places/${id}`,
  })

  async function toggleVisited(place: Place) {
    // update optimista
    place.visited = !place.visited
    try {
      await api.patch<Place>(`/places/${place.id}`, { visited: place.visited })
    } catch (err) {
      place.visited = !place.visited
      throw err
    }
  }

  return { ...base, toggleVisited }
})
