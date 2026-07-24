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
