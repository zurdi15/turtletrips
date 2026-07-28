// Traslados entre las paradas de un día del itinerario: cuánto hay de una
// actividad a la siguiente y si el día se sostiene de pie.
//
// ⚠️ Es una ESTIMACIÓN en línea recta con factor de rodeo, no una ruta real: no
// hay callejero ni horarios. El día que haya un router propio
// (`TT_ROUTING_URL` contra OSRM) bastará con devolver el mismo shape desde el
// backend y esta derivación se queda como fallback offline.
import type { ItineraryItem, Place } from '../api/types'
import { itemCoord, type Coord } from './weather'

export type TransferMode = 'walk' | 'bike' | 'transit' | 'car'

/** velocidad media puerta a puerta, ya descontando esperas y semáforos (km/h) */
export const TRANSFER_SPEEDS: Record<TransferMode, number> = {
  walk: 4.5,
  bike: 14,
  transit: 25,
  car: 45,
}

/** las calles no van en línea recta: la distancia real ronda un 30% más */
export const DETOUR_FACTOR = 1.3

/** por debajo de esto es la misma manzana: no se pinta traslado */
export const MIN_TRANSFER_KM = 0.15

/** salto que ya no se hace "de paso" entre dos visitas */
export const LONG_HAUL_KM = 300

/** rato que se está en cada parada, para estimar el largo del día sin horas */
export const DWELL_MINUTES = 60

/** día razonable de puerta a puerta */
export const MAX_DAY_MINUTES = 12 * 60

const EARTH_RADIUS_KM = 6371

/** Distancia en línea recta entre dos coordenadas (km) */
export function haversineKm(a: Coord, b: Coord): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const dLat = toRad(b.lat - a.lat)
  const dLon = toRad(b.lon - a.lon)
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)
  const h =
    Math.sin(dLat / 2) ** 2 + Math.sin(dLon / 2) ** 2 * Math.cos(lat1) * Math.cos(lat2)
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)))
}

/** Minutos estimados para recorrer una distancia en un modo */
export function travelMinutes(km: number, mode: TransferMode): number {
  return Math.round((km / TRANSFER_SPEEDS[mode]) * 60)
}

export interface Transfer {
  /** actividad de la que se sale */
  fromId: number
  /** actividad a la que se llega: la línea se pinta ENCIMA de esta fila */
  toId: number
  /** distancia estimada con rodeo (km) */
  km: number
  minutes: number
  /** salto largo: no se hace entre dos visitas sin un transporte de por medio */
  longHaul: boolean
  /**
   * El salto lo cubre una reserva de transporte de ese día. Heurística a
   * propósito tosca —cualquier salto largo de un día con vuelo o tren— porque
   * `origin`/`destination` de las reservas son texto libre y no casan con los
   * sitios. Un tramo cubierto no suma al total del día ni se juzga: su duración
   * la sabe el billete, no una estimación a velocidad urbana.
   */
  covered: boolean
}

export interface DayTransfers {
  /** traslado que PRECEDE a cada actividad, por id */
  byItem: Map<number, Transfer>
  list: Transfer[]
  /** km y minutos que te mueves POR TU CUENTA (sin los tramos cubiertos) */
  km: number
  minutes: number
}

/**
 * Traslados de un día en el orden en que están las actividades. Las que no
 * tienen sitio localizado no cortan la cadena: se mide desde la última parada
 * conocida (si no, arrastrar una nota suelta al medio borraría los traslados).
 */
export function buildDayTransfers(
  items: ItineraryItem[],
  placeById: Map<number, Place>,
  mode: TransferMode,
  ctx: { hasTransport?: boolean } = {},
): DayTransfers {
  const list: Transfer[] = []
  const byItem = new Map<number, Transfer>()
  let prev: { id: number; coord: Coord } | null = null

  for (const item of items) {
    const coord = itemCoord(item, placeById)
    if (!coord) continue
    if (prev) {
      const km = haversineKm(prev.coord, coord) * DETOUR_FACTOR
      if (km >= MIN_TRANSFER_KM) {
        const longHaul = km > LONG_HAUL_KM
        const transfer: Transfer = {
          fromId: prev.id,
          toId: item.id,
          km,
          minutes: travelMinutes(km, mode),
          longHaul,
          covered: longHaul && !!ctx.hasTransport,
        }
        list.push(transfer)
        byItem.set(item.id, transfer)
      }
    }
    prev = { id: item.id, coord }
  }

  const own = list.filter((t) => !t.covered)
  return {
    byItem,
    list,
    km: own.reduce((acc, t) => acc + t.km, 0),
    minutes: own.reduce((acc, t) => acc + t.minutes, 0),
  }
}

/** `overlap`: no da tiempo a llegar · `tooLong`: día imposible de largo ·
 *  `tooFar`: salto de otra provincia sin transporte que lo justifique */
export type DayIssue = 'overlap' | 'tooLong' | 'tooFar'

function minutesOfDay(time: string | null): number | null {
  if (!time) return null
  const [h, m] = time.split(':')
  const total = Number(h) * 60 + Number(m)
  return Number.isFinite(total) ? total : null
}

/**
 * Motivos por los que el día no cuadra. Con horas manda el reloj (¿llegas a la
 * siguiente actividad?); sin horas se estima el día entero sumando traslados y
 * un rato en cada parada. Los tramos que cubre una reserva de transporte no se
 * juzgan: con un vuelo de por medio, estimar a velocidad de autobús solo
 * produce avisos falsos.
 */
export function dayFeasibility(items: ItineraryItem[], transfers: DayTransfers): DayIssue[] {
  const issues: DayIssue[] = []
  const byId = new Map(items.map((i) => [i.id, i]))
  const own = transfers.list.filter((t) => !t.covered)

  // ¿llegas tarde a la siguiente? Solo se puede decir con horas en ambas
  let timed = false
  for (const transfer of own) {
    const from = byId.get(transfer.fromId)
    const to = byId.get(transfer.toId)
    const leave = minutesOfDay(from?.end_time ?? from?.start_time ?? null)
    const arrive = minutesOfDay(to?.start_time ?? null)
    if (leave == null || arrive == null) continue
    timed = true
    if (leave + transfer.minutes > arrive) {
      issues.push('overlap')
      break
    }
  }

  // sin horas que comparar, el aviso sale del largo estimado del día
  if (!timed) {
    // n traslados encadenan n+1 paradas; con una sola parada no hay día largo
    const stops = own.length ? own.length + 1 : 0
    if (transfers.minutes + stops * DWELL_MINUTES > MAX_DAY_MINUTES) issues.push('tooLong')
  }

  // un salto enorme solo chirría si no hay un vuelo o un tren que lo explique
  if (own.some((t) => t.longHaul)) issues.push('tooFar')

  return issues
}

/** "2,4 km" · "18 km" — bajo 10 km importa el decimal, por encima no */
export function formatKm(km: number, locale = 'es-ES'): string {
  const value = km < 10 ? Math.round(km * 10) / 10 : Math.round(km)
  return `${value.toLocaleString(locale)} km`
}

/** "45 min" · "2 h 5 min" — 'h' y 'min' valen igual en es y en en */
export function formatMinutes(minutes: number): string {
  const total = Math.max(1, Math.round(minutes))
  const h = Math.floor(total / 60)
  const m = total % 60
  if (!h) return `${m} min`
  return m ? `${h} h ${m} min` : `${h} h`
}
