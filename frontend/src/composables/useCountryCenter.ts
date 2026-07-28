import { reactive } from 'vue'
import { api } from '../api/client'
import { COUNTRY_BY_CODE } from '../countries'
import type { GeocodeResult } from '../api/types'
import { useWorldGeometry } from './useWorldGeometry'

const cache = reactive<Record<string, [number, number] | null>>({})
const pending = new Set<string>()

/**
 * Coordenadas centrales de un país. Salen del centroide de su territorio
 * principal en cuanto la geometría del mapa está cargada — instantáneo y sin
 * red. El geocoder queda de reserva para lo que no tiene polígono (Tuvalu) y
 * para las pantallas que no cargan la geometría; ojo, ese camino está limitado
 * a 1 req/s en el backend.
 *
 * Devuelve null mientras carga; es reactivo.
 */
export function useCountryCenter() {
  const { geometry, load } = useWorldGeometry()

  function centerFor(code: string | null | undefined): [number, number] | null {
    if (!code) return null
    const local = geometry.value?.centerOf(code)
    if (local) return local
    if (code in cache) return cache[code]
    if (!pending.has(code)) {
      pending.add(code)
      // la geometría puede no estar cargada todavía: se pide y, si el país
      // tiene polígono, el computed que llama aquí se recalcula con él
      load().then((geo) => {
        if (geo?.centerOf(code)) {
          pending.delete(code)
          return
        }
        const query = COUNTRY_BY_CODE.get(code)?.en ?? code
        api
          .get<GeocodeResult[]>(`/geocode?q=${encodeURIComponent(query)}`)
          .then((results) => {
            cache[code] = results.length ? [results[0].lat, results[0].lon] : null
          })
          .catch(() => (cache[code] = null))
          .finally(() => pending.delete(code))
      })
    }
    return null
  }

  return { centerFor }
}
