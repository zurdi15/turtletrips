import { reactive } from 'vue'
import { api } from '../api/client'
import { COUNTRY_BY_CODE } from '../countries'
import type { GeocodeResult } from '../api/types'

const cache = reactive<Record<string, [number, number] | null>>({})
const pending = new Set<string>()

/**
 * Coordenadas centrales de un país (vía el proxy de geocoding, cacheadas).
 * Devuelve null mientras carga; es reactivo.
 */
export function useCountryCenter() {
  function centerFor(code: string | null | undefined): [number, number] | null {
    if (!code) return null
    if (code in cache) return cache[code]
    if (!pending.has(code)) {
      pending.add(code)
      const query = COUNTRY_BY_CODE.get(code)?.en ?? code
      api
        .get<GeocodeResult[]>(`/geocode?q=${encodeURIComponent(query)}`)
        .then((results) => {
          cache[code] = results.length ? [results[0].lat, results[0].lon] : null
        })
        .catch(() => (cache[code] = null))
        .finally(() => pending.delete(code))
    }
    return null
  }
  return { centerFor }
}
