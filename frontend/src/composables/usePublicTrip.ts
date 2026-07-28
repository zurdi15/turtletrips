import { computed, ref } from 'vue'
import { ApiError, api } from '../api/client'
import type { Booking, ItineraryItem, Place, PublicTrip } from '../api/types'

/**
 * Viaje compartido por enlace. No toca la sesión ni las stores: quien abre
 * /s/{token} puede no tener cuenta en la instancia, así que aquí no hay
 * `ensureLoaded`, ni caché, ni escritura de ningún tipo.
 */
export function usePublicTrip() {
  const trip = ref<PublicTrip | null>(null)
  const loading = ref(true)
  /** el enlace ya no vale (404): revocado, rotado o inventado */
  const gone = ref(false)
  /** no se pudo ni preguntar: red caída, proxy, 500… se puede reintentar */
  const failed = ref(false)
  let lastToken = ''

  async function load(token: string) {
    lastToken = token
    loading.value = true
    gone.value = false
    failed.value = false
    try {
      trip.value = await api.get<PublicTrip>(`/public/trips/${encodeURIComponent(token)}`)
    } catch (err) {
      trip.value = null
      // el 404 es el caso normal (enlace revocado); cualquier otra cosa es un
      // fallo temporal y NO se le puede decir al visitante que le han quitado
      // el acceso
      if (err instanceof ApiError && err.status === 404) gone.value = true
      else failed.value = true
    } finally {
      loading.value = false
    }
  }

  const retry = () => load(lastToken)

  // El enlace trae tipos propios (sin dinero, códigos ni notas privadas). Para
  // reutilizar el mapa y las derivaciones de la agenda se completan con NULOS
  // los campos que no viajan: la lista es, literalmente, lo que NO contiene.
  const bookings = computed<Booking[]>(() =>
    (trip.value?.bookings ?? []).map((b) => ({
      ...b,
      trip_id: 0,
      confirmation_code: null,
      flight_number: null,
      cost_amount: null,
      cost_currency: null,
      notes: null,
      paid_by_id: null,
      paid_by_common: false,
    })),
  )
  const places = computed<Place[]>(() =>
    (trip.value?.places ?? []).map((p) => ({
      ...p,
      trip_id: 0,
      notes: null,
      visited: false,
      priority: 0,
    })),
  )
  const items = computed<ItineraryItem[]>(() =>
    (trip.value?.itinerary ?? []).map((i) => ({ ...i, trip_id: 0 })),
  )

  return { trip, loading, gone, failed, load, retry, bookings, places, items }
}
