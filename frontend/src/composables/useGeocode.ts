import { ref } from 'vue'
import { api } from '../api/client'
import type { GeocodeResult } from '../api/types'

export function useGeocodeSearch() {
  const results = ref<GeocodeResult[]>([])
  const loading = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined

  function search(query: string) {
    if (timer) clearTimeout(timer)
    if (query.trim().length < 3) {
      results.value = []
      return
    }
    timer = setTimeout(async () => {
      loading.value = true
      try {
        results.value = await api.get<GeocodeResult[]>(
          `/geocode?q=${encodeURIComponent(query.trim())}`,
        )
      } catch {
        results.value = []
      } finally {
        loading.value = false
      }
    }, 450)
  }

  return { results, loading, search }
}

/**
 * Lugar más cercano a un punto fijado a mano en el mapa; null si no hay nada
 * (alta mar) o falla la red — el pin vale igual, solo se queda sin dirección.
 */
export async function reverseGeocode(lat: number, lon: number): Promise<GeocodeResult | null> {
  try {
    return await api.get<GeocodeResult>(`/geocode/reverse?lat=${lat}&lon=${lon}`)
  } catch {
    return null
  }
}
