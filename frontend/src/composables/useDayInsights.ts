import { computed, ref, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Booking, ItineraryItem, Place, Trip } from '../api/types'
import { TRANSFER_MODE_ICONS, TRANSFER_MODE_KEYS } from '../constants'
import { intlLocale } from '../i18n'
import { hasLodgingBookings, lodgingCoverage } from '../utils/lodging'
import type { TransportEntry } from '../utils/itinerary'
import {
  buildDayTransfers,
  dayFeasibility,
  formatKm,
  formatMinutes,
  type TransferMode,
} from '../utils/transfers'

/**
 * Lo que la agenda sabe decir de cada día sin preguntarle a nadie: si esa noche
 * hay cama y cuánto hay que moverse. Todo sale de funciones puras
 * (`utils/lodging.ts` y `utils/transfers.ts`); esto solo las ata al estado de la
 * pestaña.
 *
 * Los traslados se calculan sobre el ESPEJO LOCAL de la lista (`lists[day]`), no
 * sobre el store: así se recalculan mientras arrastras, sin esperar al PATCH.
 */
export function useDayInsights(input: {
  trip: () => Trip
  days: Ref<string[]>
  lists: Record<string, ItineraryItem[]>
  bookings: () => Booking[]
  placeById: Ref<Map<number, Place>>
  transportsByDay: Ref<Map<string, TransportEntry[]>>
}) {
  const { t } = useI18n()

  // noches del viaje sin cama: se avisa en la cabecera del día en que te
  // acuestas, y solo si el viaje lleva alojamiento apuntado (si no, un viaje
  // durmiendo en casa de alguien saldría entero en rojo)
  const lodgingGaps = computed(() =>
    hasLodgingBookings(input.bookings())
      ? lodgingCoverage(input.trip(), input.bookings()).gapNights
      : new Set<string>(),
  )

  const transferMode = ref<TransferMode>('transit')
  const transferModeOptions = computed(() =>
    (Object.keys(TRANSFER_MODE_KEYS) as TransferMode[]).map((mode) => ({
      value: mode,
      label: t(TRANSFER_MODE_KEYS[mode]),
      icon: TRANSFER_MODE_ICONS[mode],
    })),
  )

  const transfersByDay = computed(
    () =>
      new Map(
        input.days.value.map((day) => [
          day,
          buildDayTransfers(input.lists[day] ?? [], input.placeById.value, transferMode.value, {
            hasTransport: (input.transportsByDay.value.get(day) ?? []).length > 0,
          }),
        ]),
      ),
  )

  const issuesByDay = computed(
    () =>
      new Map(
        input.days.value.map((day) => [
          day,
          dayFeasibility(input.lists[day] ?? [], transfersByDay.value.get(day)!),
        ]),
      ),
  )

  /** "12 km · 1 h 20 min" del día, o null si no te mueves por tu cuenta */
  function transferSummary(day: string): string | null {
    const own = transfersByDay.value.get(day)
    // un día entero cubierto por un tren no tiene total propio que enseñar
    if (!own?.list.some((transfer) => !transfer.covered)) return null
    return `${formatKm(own.km, intlLocale())} · ${formatMinutes(own.minutes)}`
  }

  function issuesTooltip(day: string): string {
    return (issuesByDay.value.get(day) ?? [])
      .map((issue) => t(`itinerary.transfers.issues.${issue}`))
      .join(' · ')
  }

  return {
    lodgingGaps,
    transferMode,
    transferModeOptions,
    transfersByDay,
    issuesByDay,
    transferSummary,
    issuesTooltip,
  }
}
