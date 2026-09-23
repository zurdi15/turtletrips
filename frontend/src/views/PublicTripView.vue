<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import PlaceMap from '../components/PlaceMap.vue'
import TabSkeleton from '../components/TabSkeleton.vue'
import EmptyState from '../components/EmptyState.vue'
import type { AgendaRow } from '../components/itinerary/AgendaBookingSection.vue'
import PublicAgendaDay from '../components/share/PublicAgendaDay.vue'
import PublicTripHero from '../components/share/PublicTripHero.vue'
import type { ItineraryItem } from '../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_KEYS } from '../constants'
import { applyVisitorLocale } from '../i18n'
import { usePublicTrip } from '../composables/usePublicTrip'
import { useDayInsights } from '../composables/useDayInsights'
import { useWeather } from '../composables/useWeather'
import { formatDateTime } from '../composables/useMoney'
import {
  agendaDayLabel,
  agendaDays,
  bookingHead,
  buildLodgingByDay,
  buildOtherBookingsByDay,
  buildContinuations,
  buildRoute,
  buildTransportsByDay,
  lodgingHead,
  transportHead,
  transportKey,
  transportLabel,
  transportRowView,
} from '../utils/itinerary'
import { itemCoord, pickDayCoords, sameForecast, type Coord } from '../utils/weather'

const props = defineProps<{ token: string }>()

const { t } = useI18n()
const { trip, loading, gone, failed, load, retry, bookings, places, items } = usePublicTrip()

onMounted(() => {
  // el invitado no tiene cuenta ni preferencia guardada: manda su navegador
  applyVisitorLocale()
  load(props.token)
})

const placeById = computed(() => new Map(places.value.map((p) => [p.id, p])))
const transportsByDay = computed(() => buildTransportsByDay(bookings.value))
const otherBookingsByDay = computed(() => buildOtherBookingsByDay(bookings.value))
const lodgingByDay = computed(() => buildLodgingByDay(bookings.value))
const itemsByDay = computed(() => {
  const map = new Map<string, ItineraryItem[]>()
  for (const item of items.value) map.set(item.day, [...(map.get(item.day) ?? []), item])
  return map
})

const continuations = computed(() => buildContinuations(items.value))

const days = computed(() =>
  trip.value
    ? agendaDays(
        trip.value,
        items.value,
        transportsByDay.value,
        otherBookingsByDay.value,
        lodgingByDay.value,
      )
    : [],
)

// ---- previsión: igual que en la app (cabecera = alojamiento de la noche, cada
// actividad la de su sitio), pero pedida por el token del enlace ----
const dayCoords = computed(() => pickDayCoords(days.value, lodgingByDay.value, placeById.value))
const weatherRequests = computed(() => {
  const requests: { day: string; coord: Coord }[] = []
  for (const [day, coord] of dayCoords.value) requests.push({ day, coord })
  for (const day of days.value) {
    for (const item of itemsByDay.value.get(day) ?? []) {
      const coord = itemCoord(item, placeById.value)
      if (coord) requests.push({ day, coord })
    }
  }
  return requests
})
const { forecastAt } = useWeather(
  () => weatherRequests.value,
  `/public/trips/${encodeURIComponent(props.token)}/weather`,
)

function headerForecast(day: string) {
  return forecastAt(day, dayCoords.value.get(day))
}
// la de cada actividad solo si dice algo distinto que la de la cabecera
function itemForecast(day: string, item: ItineraryItem) {
  const own = forecastAt(day, itemCoord(item, placeById.value))
  const header = headerForecast(day)
  return own && header && sameForecast(own, header) ? null : own
}

// avisos del día (cama y traslados): el mismo composable que la agenda de la app
const lists = reactive<Record<string, ItineraryItem[]>>({})
watch(
  [items, days],
  () => {
    for (const key of Object.keys(lists)) delete lists[key]
    for (const day of days.value) lists[day] = (itemsByDay.value.get(day) ?? []).slice()
  },
  { immediate: true, deep: true },
)

const { lodgingGaps, transferMode, transfersByDay, issuesByDay, transferSummary } = useDayInsights({
  trip: () => trip.value ?? { start_date: null, end_date: null },
  days,
  lists,
  bookings: () => bookings.value,
  placeById,
  transportsByDay,
})

// filas de las tres bandas de reservas, como en la agenda de la app (sin los
// chips de sitio/gasto/reserva, que llevan a pantallas con sesión)
function transportRows(day: string): AgendaRow[] {
  return (transportsByDay.value.get(day) ?? []).map((e) => ({
    key: transportKey(e),
    head: transportHead(e, t),
    label: transportLabel(e),
    transport: transportRowView(e, t),
    bookingId: e.b.id,
    bookingTitle: e.b.title,
    placeId: null,
    expenseId: null,
  }))
}
function otherRows(day: string): AgendaRow[] {
  return (otherBookingsByDay.value.get(day) ?? []).map((b) => ({
    key: `o-${b.id}`,
    head: bookingHead(b, t),
    label: b.title,
    bookingId: b.id,
    bookingTitle: b.title,
    placeId: null,
    expenseId: null,
  }))
}
function lodgingRows(day: string): AgendaRow[] {
  return (lodgingByDay.value.get(day) ?? []).map((b) => ({
    key: `l-${b.id}`,
    head: lodgingHead(b, day, t),
    label: b.title,
    bookingId: b.id,
    bookingTitle: b.title,
    placeId: null,
    expenseId: null,
  }))
}

const agenda = computed(() =>
  days.value.map((day) => ({ day, ...agendaDayLabel(day, trip.value?.start_date ?? null, t) })),
)

const route = computed(() => buildRoute(items.value, placeById.value))
const has = (scope: string) => !!trip.value?.scopes.includes(scope as never)
</script>

<template>
  <!-- sin ancho ni padding propios: esta vista ya vive dentro del <main> de
       App.vue (max-w-6xl + px-4), y al sumar otro px-4 las tarjetas salían 32px
       más estrechas que en la app y recortaban las rutas ("MAD → A…") -->
  <div class="flex flex-col gap-8 pb-4">
    <TabSkeleton v-if="loading" variant="cards" :rows="3" />

    <EmptyState
      v-else-if="failed"
      icon="pi pi-exclamation-triangle"
      :title="t('share.public.errorTitle')"
      :subtitle="t('share.public.errorSubtitle')"
    >
      <Button :label="t('share.public.retry')" icon="pi pi-refresh" outlined @click="retry" />
    </EmptyState>

    <EmptyState
      v-else-if="gone || !trip"
      icon="pi pi-link"
      :title="t('share.public.goneTitle')"
      :subtitle="t('share.public.goneSubtitle')"
    />

    <template v-else>
      <PublicTripHero :trip="trip" :printTo="`/s/${token}/print`" />

      <section v-if="has('itinerary') && agenda.length" class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink-secondary uppercase tracking-wide">
          {{ t('trips.tabs.itinerary') }}
        </h2>
        <div class="tt-stagger flex flex-col gap-3">
          <PublicAgendaDay
            v-for="entry in agenda"
            :key="entry.day"
            :title="entry.title"
            :sub="entry.sub"
            :issues="issuesByDay.get(entry.day) ?? []"
            :lodgingGap="lodgingGaps.has(entry.day)"
            :transfers="transferSummary(entry.day)"
            :forecast="headerForecast(entry.day)"
            :transportRows="transportRows(entry.day)"
            :otherRows="otherRows(entry.day)"
            :lodgingRows="lodgingRows(entry.day)"
            :items="lists[entry.day] ?? []"
            :continuations="continuations.get(entry.day) ?? []"
            :placeById="placeById"
            :itemForecast="(item) => itemForecast(entry.day, item)"
            :transferOf="(item) => transfersByDay.get(entry.day)?.byItem.get(item.id) ?? null"
            :transferMode="transferMode"
            :emptyLabel="t('share.public.emptyDay')"
          />
        </div>
      </section>

      <section v-if="has('map') && places.length" class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink-secondary uppercase tracking-wide">
          {{ t('trips.tabs.places') }}
        </h2>
        <div class="bg-surface rounded-card border border-line p-2 h-80">
          <PlaceMap :places="places" :route="route" :countryCode="trip.countries[0]" />
        </div>
        <ul class="tt-stagger grid sm:grid-cols-2 gap-2">
          <!-- min-w-0: sin él una dirección larga estira su celda de la rejilla
               (que mide por max-content) y con ella la página entera -->
          <li
            v-for="place in places"
            :key="place.id"
            class="bg-surface rounded-card border border-line px-3 py-2 min-w-0"
          >
            <p class="text-sm font-medium text-ink break-words">{{ place.name }}</p>
            <!-- la dirección se parte en varias líneas: a quien recibe el enlace
                 le sirve entera, no cortada con puntos suspensivos -->
            <p v-if="place.address" class="text-xs text-ink-faint break-words">{{ place.address }}</p>
            <a
              v-if="place.url"
              :href="place.url"
              target="_blank"
              rel="noopener noreferrer"
              class="text-xs text-info hover:underline"
            >
              {{ t('share.public.placeLink') }}
            </a>
          </li>
        </ul>
      </section>

      <section v-if="has('bookings') && bookings.length" class="flex flex-col gap-3">
        <h2 class="text-sm font-semibold text-ink-secondary uppercase tracking-wide">
          {{ t('trips.tabs.bookings') }}
        </h2>
        <ul class="tt-stagger flex flex-col gap-2">
          <li
            v-for="booking in bookings"
            :key="booking.id"
            class="bg-surface rounded-card border border-line px-3 py-2 flex items-start gap-3"
          >
            <i :class="BOOKING_TYPE_ICONS[booking.type]" class="text-ink-faint mt-0.5" />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-medium text-ink">{{ booking.title }}</p>
              <p class="text-xs text-ink-faint">
                {{ t(BOOKING_TYPE_KEYS[booking.type]) }}
                <template v-if="booking.start_dt"> · {{ formatDateTime(booking.start_dt) }}</template>
                <template v-if="booking.provider"> · {{ booking.provider }}</template>
                <template v-if="booking.flight_number"> · {{ booking.flight_number }}</template>
              </p>
              <!-- con tramos, una línea por vuelo/tren con sus horas -->
              <template v-if="booking.segments.length">
                <p v-for="seg in booking.segments" :key="seg.id" class="text-xs text-ink-muted">
                  {{ seg.origin ?? '?' }} → {{ seg.destination ?? '?' }}
                  <template v-if="seg.departure_dt">
                    · {{ formatDateTime(seg.departure_dt) }}
                    <template v-if="seg.arrival_dt"> → {{ formatDateTime(seg.arrival_dt) }}</template>
                  </template>
                  <template v-if="seg.flight_number">
                    · <span class="font-mono">{{ seg.flight_number }}</span>
                  </template>
                </p>
              </template>
              <p v-else-if="booking.origin || booking.destination" class="text-xs text-ink-muted">
                {{ booking.origin ?? '?' }} → {{ booking.destination ?? '?' }}
              </p>
              <p v-if="booking.address" class="text-xs text-ink-faint break-words">
                {{ booking.address }}
              </p>
            </div>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>
