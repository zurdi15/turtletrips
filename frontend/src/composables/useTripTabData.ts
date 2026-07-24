import { onMounted, watch } from 'vue'
import type { Trip } from '../api/types'

interface TripTabDataOptions {
  /** carga los stores que necesita la pestaña; puede devolver promesa */
  load: (tripId: number) => void | Promise<unknown>
  /** tras la PRIMERA carga (esperada si load devuelve promesa): highlight
   *  desde ?query, scroll, selección inicial… */
  afterFirstLoad?: () => void | Promise<void>
}

/**
 * Preámbulo de datos común a todas las pestañas de un viaje: cargar al
 * montarse y recargar si cambia el viaje (misma vista, otro trip.id).
 */
export function useTripTabData(trip: () => Trip, opts: TripTabDataOptions): void {
  onMounted(async () => {
    await opts.load(trip().id)
    await opts.afterFirstLoad?.()
  })
  watch(
    () => trip().id,
    (tripId) => opts.load(tripId),
  )
}
