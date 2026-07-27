import type { Booking, ItineraryItem, Place } from '../api/types'

export interface Coord {
  lat: number
  lon: number
}

/** icono mdi para cada código WMO de Open-Meteo (agrupados por familia) */
export function weatherIcon(code: number): string {
  if (code === 0) return 'mdi mdi-weather-sunny'
  if (code <= 2) return 'mdi mdi-weather-partly-cloudy'
  if (code === 3) return 'mdi mdi-weather-cloudy'
  if (code === 45 || code === 48) return 'mdi mdi-weather-fog'
  if (code >= 51 && code <= 57) return 'mdi mdi-weather-partly-rainy'
  if (code === 61 || code === 63 || code === 66) return 'mdi mdi-weather-rainy'
  if (code === 65 || code === 67 || (code >= 80 && code <= 82)) return 'mdi mdi-weather-pouring'
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'mdi mdi-weather-snowy'
  if (code >= 95) return 'mdi mdi-weather-lightning-rainy'
  return 'mdi mdi-weather-partly-cloudy'
}

/** clave de agrupación: ~11 km de resolución, suficiente para previsión diaria */
export function coordKey(c: Coord): string {
  return `${c.lat.toFixed(1)}:${c.lon.toFixed(1)}`
}

function bookingCoord(b: Booking, placeById: Map<number, Place>): Coord | null {
  if (b.lat != null && b.lon != null) return { lat: b.lat, lon: b.lon }
  const place = b.place_id != null ? placeById.get(b.place_id) : undefined
  if (place?.lat != null && place.lon != null) return { lat: place.lat, lon: place.lon }
  return null
}

/**
 * Coordenada de la cabecera de cada día: SOLO el alojamiento de esa noche
 * (lodgingByDay ya reparte la estancia en todas sus noches, así que las
 * cabeceras de los días "sigue" también la llevan). Las actividades tienen su
 * previsión propia por sitio — un mismo día puede tocar varias zonas.
 */
export function pickDayCoords(
  days: string[],
  lodgingByDay: Map<string, Booking[]>,
  placeById: Map<number, Place>,
): Map<string, Coord> {
  const result = new Map<string, Coord>()
  for (const day of days) {
    for (const booking of lodgingByDay.get(day) ?? []) {
      const coord = bookingCoord(booking, placeById)
      if (coord) {
        result.set(day, coord)
        break
      }
    }
  }
  return result
}

/** coordenada del sitio de una actividad (null si no está localizada) */
export function itemCoord(item: ItineraryItem, placeById: Map<number, Place>): Coord | null {
  const place = item.place_id != null ? placeById.get(item.place_id) : undefined
  if (place?.lat != null && place.lon != null) return { lat: place.lat, lon: place.lon }
  return null
}
