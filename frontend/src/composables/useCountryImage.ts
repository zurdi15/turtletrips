import { reactive } from 'vue'
import { api } from '../api/client'
import { COUNTRY_BY_CODE } from '../countries'

const cache = reactive<Record<string, string | null>>({})
const pending = new Set<string>()

/**
 * URL de imagen hero para un país (banner de Wikivoyage vía backend).
 * Devuelve null mientras carga o si no hay imagen; es reactivo.
 */
export function useCountryImage() {
  function imageFor(code: string | undefined): string | null {
    if (!code) return null
    if (code in cache) return cache[code]
    if (!pending.has(code)) {
      pending.add(code)
      const query = COUNTRY_BY_CODE.get(code)?.en ?? code
      api
        .get<{ image_url: string | null }>(`/country-image?q=${encodeURIComponent(query)}`)
        .then((r) => (cache[code] = r.image_url))
        .catch(() => (cache[code] = null))
        .finally(() => pending.delete(code))
    }
    return null
  }
  return { imageFor }
}
