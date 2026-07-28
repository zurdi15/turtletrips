// Agenda del viaje COMPARTIDO: una fila por cosa que pasa ese día, sin
// enlaces, sin acciones y sin nada que no viaje en el enlace público.
//
// Reutiliza las cabeceras de utils/itinerary.ts ("Vuelo: 07:30", "Check-in:
// 15:00") para que el plan compartido se lea igual que dentro de la app.
import type { Booking, ItineraryItem, Place } from '../api/types'
import { BOOKING_TYPE_ICONS } from '../constants'
import {
  bookingHead,
  fmtTime,
  lodgingHead,
  transportHead,
  transportLabel,
  type TransportEntry,
  type TranslateFn,
} from './itinerary'

export type RowTone = 'info' | 'warn' | 'lodging' | 'plain'

export interface PublicDayRow {
  key: string
  /** columna izquierda: hora o tipo con hora */
  head: string
  title: string
  /** sitio enlazado (null si la actividad ya se llama igual que él) */
  place: string | null
  /** nota libre; la agenda compartida solo la enseña si no hay sitio, la
   *  versión imprimible puede enseñar las dos */
  note: string | null
  tone: RowTone
  icon: string | null
}

function placeName(id: number | null, placeById: Map<number, Place>): string | null {
  return id == null ? null : (placeById.get(id)?.name ?? null)
}

/** Hora de una actividad ("10:00 – 12:00"), o vacío si no la tiene */
function itemHead(item: ItineraryItem): string {
  if (!item.start_time) return ''
  const end = item.end_time ? `–${fmtTime(item.end_time)}` : ''
  return `${fmtTime(item.start_time)}${end}`
}

/**
 * Filas de un día en el mismo orden que la agenda de la app: cómo llegas
 * (transporte), qué tienes reservado, qué vais a hacer y dónde dormís.
 */
export function buildPublicDay(
  day: string,
  items: ItineraryItem[],
  transports: TransportEntry[],
  otherBookings: Booking[],
  lodging: Booking[],
  placeById: Map<number, Place>,
  t: TranslateFn,
): PublicDayRow[] {
  const rows: PublicDayRow[] = []

  for (const entry of transports) {
    rows.push({
      key: `t-${entry.b.id}-${entry.arrival ? 'a' : 's'}`,
      head: transportHead(entry, t),
      title: transportLabel(entry),
      place: entry.b.provider,
      note: null,
      tone: 'info',
      icon: BOOKING_TYPE_ICONS[entry.b.type],
    })
  }

  for (const booking of otherBookings) {
    rows.push({
      key: `o-${booking.id}`,
      head: bookingHead(booking, t),
      title: booking.title,
      place: booking.provider,
      note: null,
      tone: 'warn',
      icon: BOOKING_TYPE_ICONS[booking.type],
    })
  }

  for (const item of items) {
    // el sitio, salvo que la actividad se llame igual que él ("Sagrada Família
    // / Sagrada Família" no aporta nada)
    const place = placeName(item.place_id, placeById)
    rows.push({
      key: `i-${item.id}`,
      head: itemHead(item),
      title: item.title,
      place: place && place !== item.title ? place : null,
      note: item.notes,
      tone: 'plain',
      icon: null,
    })
  }

  for (const booking of lodging) {
    rows.push({
      key: `l-${booking.id}`,
      head: lodgingHead(booking, day, t),
      title: booking.title,
      place: null,
      note: null,
      tone: 'lodging',
      icon: BOOKING_TYPE_ICONS.hotel,
    })
  }

  return rows
}
