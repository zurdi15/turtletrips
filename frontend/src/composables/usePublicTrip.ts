import { ref } from 'vue'
import { ApiError, api } from '../api/client'
import type { PublicTrip } from '../api/types'

/**
 * Viaje compartido por enlace. No toca la sesión ni las stores: quien abre
 * /s/{token} puede no tener cuenta en la instancia, así que aquí no hay
 * `ensureLoaded`, ni caché, ni escritura de ningún tipo.
 */
export function usePublicTrip() {
  const trip = ref<PublicTrip | null>(null)
  const loading = ref(true)
  const gone = ref(false)

  async function load(token: string) {
    loading.value = true
    gone.value = false
    try {
      trip.value = await api.get<PublicTrip>(`/public/trips/${encodeURIComponent(token)}`)
    } catch (err) {
      trip.value = null
      // 404 = enlace inválido, rotado o dejado de compartir: es el caso normal,
      // no un error que enseñar con un toast
      gone.value = err instanceof ApiError && err.status === 404
      if (!gone.value) throw err
    } finally {
      loading.value = false
    }
  }

  return { trip, loading, gone, load }
}
