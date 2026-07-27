import { ref, watch } from 'vue'
import { api } from '../api/client'
import type { DayForecast } from '../api/types'
import { coordKey, type Coord } from '../utils/weather'

/**
 * Previsión por (día, coordenada): la cabecera del día usa el alojamiento y
 * cada actividad su propio sitio. Las peticiones se agrupan por coordenada
 * redondeada (~11 km) y rango de días — UNA petición por zona; el backend
 * recorta al horizonte de Open-Meteo (viajes pasados o lejanos → vacío).
 * Best-effort: los errores se tragan y la agenda sigue igual.
 */
export function useWeather(requests: () => { day: string; coord: Coord }[]) {
  // clave `${coordKey}|${day}` → previsión de ese día en esa zona
  const forecasts = ref(new Map<string, DayForecast>())
  const requested = new Set<string>()

  watch(
    requests,
    async (reqs) => {
      const groups = new Map<string, { coord: Coord; days: Set<string> }>()
      for (const { day, coord } of reqs) {
        const key = coordKey(coord)
        const group = groups.get(key) ?? { coord, days: new Set() }
        group.days.add(day)
        groups.set(key, group)
      }
      for (const [key, group] of groups) {
        const days = [...group.days].sort()
        const reqKey = `${key}:${days[0]}:${days[days.length - 1]}`
        if (requested.has(reqKey)) continue
        requested.add(reqKey)
        try {
          const result = await api.get<DayForecast[]>(
            `/weather?lat=${group.coord.lat}&lon=${group.coord.lon}` +
              `&start=${days[0]}&end=${days[days.length - 1]}`,
          )
          const next = new Map(forecasts.value)
          for (const forecast of result) next.set(`${key}|${forecast.day}`, forecast)
          forecasts.value = next
        } catch {
          // sin previsión no pasa nada
        }
      }
    },
    { immediate: true },
  )

  function forecastAt(day: string, coord: Coord | null | undefined): DayForecast | undefined {
    return coord ? forecasts.value.get(`${coordKey(coord)}|${day}`) : undefined
  }

  return { forecastAt }
}
