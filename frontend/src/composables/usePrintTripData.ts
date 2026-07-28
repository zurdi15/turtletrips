import { computed, type Ref } from 'vue'
import type { Booking, ItineraryItem, Place } from '../api/types'
import type { PrintTrip } from '../components/print/TripPrintDocument.vue'
import {
  agendaDayLabel,
  agendaDays,
  buildLodgingByDay,
  buildOtherBookingsByDay,
  buildRoute,
  buildTransportsByDay,
  type TranslateFn,
} from '../utils/itinerary'
import { buildPublicDay } from '../utils/publicAgenda'
import { printSections, type PrintOptions } from '../utils/print'

/**
 * Derivación compartida por las dos vistas imprimibles (la del viaje y la del
 * enlace público): días de la agenda, ruta del mapa y secciones con contenido.
 * Las fuentes llegan como funciones para que sirva igual con stores que con el
 * resultado de `usePublicTrip`.
 */
export function usePrintTripData(input: {
  trip: () => PrintTrip | null
  places: () => Place[]
  items: () => ItineraryItem[]
  bookings: () => Booking[]
  hasExpenses: () => boolean
  options: Ref<PrintOptions>
  t: TranslateFn
}) {
  const trip = computed(input.trip)
  const places = computed(input.places)
  const items = computed(input.items)
  const bookings = computed(input.bookings)

  const placeById = computed(() => new Map(places.value.map((place) => [place.id, place])))
  const transportsByDay = computed(() => buildTransportsByDay(bookings.value))
  const otherBookingsByDay = computed(() => buildOtherBookingsByDay(bookings.value))
  const lodgingByDay = computed(() => buildLodgingByDay(bookings.value))
  const itemsByDay = computed(() => {
    const map = new Map<string, ItineraryItem[]>()
    for (const item of items.value) map.set(item.day, [...(map.get(item.day) ?? []), item])
    return map
  })

  const days = computed(() => {
    const current = trip.value
    if (!current) return []
    return agendaDays(
      current,
      items.value,
      transportsByDay.value,
      otherBookingsByDay.value,
      lodgingByDay.value,
    ).map((day) => ({
      day,
      ...agendaDayLabel(day, current.start_date, input.t),
      rows: buildPublicDay(
        day,
        itemsByDay.value.get(day) ?? [],
        transportsByDay.value.get(day) ?? [],
        otherBookingsByDay.value.get(day) ?? [],
        lodgingByDay.value.get(day) ?? [],
        placeById.value,
        input.t,
      ),
    }))
  })

  const route = computed(() => buildRoute(items.value, placeById.value))

  const sections = computed(() =>
    printSections(input.options.value, {
      days: days.value.length,
      places: places.value.length,
      locatedPlaces: places.value.filter((place) => place.lat != null && place.lon != null).length,
      bookings: bookings.value.length,
      hasExpenses: input.hasExpenses(),
    }),
  )

  return { trip, days, route, sections }
}
