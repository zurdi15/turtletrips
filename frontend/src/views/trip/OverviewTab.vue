<script setup lang="ts">
import { computed } from 'vue'
import Button from 'primevue/button'
import PlaceMap from '../../components/PlaceMap.vue'
import LodgingGapsCard from '../../components/trip/LodgingGapsCard.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import ProgressMeter from '../../components/ui/ProgressMeter.vue'
import type { Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_KEYS } from '../../constants'
import { useExpensesStore } from '../../stores/expenses'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { useItineraryStore } from '../../stores/itinerary'
import { buildRoute } from '../../utils/itinerary'
import { layoverInfo, segmentLabel, upcomingBookings } from '../../utils/segments'
import { formatDateTime, formatMoney } from '../../composables/useMoney'
import { useTripTabData } from '../../composables/useTripTabData'
import { DAY_MS, daysBetween, daysUntil } from '../../utils/dates'
import { budgetPercent } from '../../utils/expenses'

const props = defineProps<{ trip: Trip }>()
const expenses = useExpensesStore()
const places = usePlacesStore()
const bookings = useBookingsStore()
const itinerary = useItineraryStore()

useTripTabData(() => props.trip, {
  load(tripId) {
    expenses.load(tripId)
    places.load(tripId)
    bookings.load(tripId)
    itinerary.load(tripId)
  },
})

// ruta del itinerario sobre el mapa del resumen
const route = computed(() =>
  buildRoute(itinerary.items, new Map(places.items.map((p) => [p.id, p]))),
)

const daysToStart = computed(() => daysUntil(props.trip.start_date))

const tripDays = computed(() => {
  if (!props.trip.start_date || !props.trip.end_date) return null
  return daysBetween(props.trip.start_date, props.trip.end_date) + 1
})

const budgetPct = computed(() => budgetPercent(expenses.summary))

const visitedCount = computed(() => places.items.filter((p) => p.visited).length)

// una reserva con tramos aporta una entrada por TRAYECTO: la vuelta sigue
// saliendo aquí aunque la ida ya haya volado. Solo a 7 días vista: esto es
// el "qué me toca ya", no la lista entera de reservas
const nextBookings = computed(() =>
  upcomingBookings(bookings.items, Date.now(), DAY_MS, 7 * DAY_MS).slice(0, 4),
)

// horas "10:45" de un tramo para el desglose (00:00 = sin hora, como siempre)
function segTime(dt: string | null): string | null {
  if (!dt) return null
  const time = dt.slice(11, 16)
  return time !== '00:00' ? time : null
}

function segPlusDays(seg: { departure_dt: string | null; arrival_dt: string | null }): number {
  if (!seg.departure_dt || !seg.arrival_dt) return 0
  return Math.max(0, daysBetween(seg.departure_dt.slice(0, 10), seg.arrival_dt.slice(0, 10)))
}

// primera visita al viaje: todo cargando y sin datos aún
const initialLoading = computed(
  () =>
    (expenses.loading || places.loading || bookings.loading) &&
    !expenses.items.length &&
    !places.items.length &&
    !bookings.items.length,
)
</script>

<template>
  <div v-if="initialLoading" class="flex flex-col gap-5">
    <TabSkeleton variant="stats" />
    <TabSkeleton variant="cards" :rows="2" />
  </div>
  <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2 flex flex-col gap-6">
      <div class="tt-stagger grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="bg-surface rounded-card border border-line p-4 text-center">
          <p class="text-2xl font-bold text-ink-heading">{{ tripDays ?? '—' }}</p>
          <p class="text-xs text-ink-faint mt-1">{{ $t('trips.stats.tripDays') }}</p>
        </div>
        <div class="bg-surface rounded-card border border-line p-4 text-center">
          <p class="text-2xl font-bold" :class="daysToStart != null ? 'text-info' : 'text-ink-heading'">
            {{ daysToStart ?? '—' }}
          </p>
          <p class="text-xs text-ink-faint mt-1">{{ $t('trips.stats.daysToStart') }}</p>
        </div>
        <div class="bg-surface rounded-card border border-line p-4 text-center">
          <p class="text-2xl font-bold text-ink-heading">{{ visitedCount }}/{{ places.items.length }}</p>
          <p class="text-xs text-ink-faint mt-1">{{ $t('trips.stats.placesVisited') }}</p>
        </div>
        <div class="bg-surface rounded-card border border-line p-4 text-center">
          <p class="text-2xl font-bold text-ink-heading">{{ bookings.items.length }}</p>
          <p class="text-xs text-ink-faint mt-1">{{ $t('trips.stats.bookings') }}</p>
        </div>
      </div>

      <LodgingGapsCard :trip="trip" :bookings="bookings.items" />

      <div class="bg-surface rounded-card border border-line p-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-ink-secondary">{{ $t('trips.overview.budget') }}</h3>
          <router-link :to="{ name: 'trip-expenses', params: { id: trip.id } }">
            <Button
              :label="$t('trips.overview.viewExpenses')"
              text
              size="small"
              severity="warn"
              icon="pi pi-arrow-right"
              iconPos="right"
            />
          </router-link>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-2xl font-bold text-ink-heading">
            {{ formatMoney(expenses.summary?.total_base ?? 0, trip.base_currency) }}
          </span>
          <span v-if="expenses.summary?.budget_amount" class="text-sm text-ink-faint">
            {{
              $t('trips.overview.ofBudget', {
                amount: formatMoney(expenses.summary.budget_amount, trip.base_currency),
              })
            }}
          </span>
        </div>
        <div v-if="budgetPct != null" class="mt-3">
          <ProgressMeter :value="budgetPct" thresholds size="md" />
        </div>
        <p v-else class="text-xs text-ink-faint mt-2">
          {{ $t('trips.overview.noBudgetHint') }}
        </p>
      </div>

      <div class="bg-surface rounded-card border border-line p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-ink-secondary">
            {{ $t('trips.overview.nextBookings') }}
          </h3>
          <router-link :to="{ name: 'trip-bookings', params: { id: trip.id } }">
            <Button
              :label="$t('trips.overview.viewBookings')"
              text
              size="small"
              severity="info"
              icon="pi pi-arrow-right"
              iconPos="right"
            />
          </router-link>
        </div>
        <div v-if="nextBookings.length" class="tt-stagger flex flex-col gap-2">
          <div
            v-for="entry in nextBookings"
            :key="`${entry.b.id}-${entry.dt}`"
            class="flex items-start gap-3 p-2 rounded-lg bg-surface-soft"
          >
            <i :class="BOOKING_TYPE_ICONS[entry.b.type]" class="text-ink-faint mt-0.5" />
            <div class="flex-1 min-w-0">
              <p class="font-medium text-sm text-ink truncate">{{ entry.b.title }}</p>
              <p class="text-xs text-ink-faint truncate">
                {{ $t(BOOKING_TYPE_KEYS[entry.b.type])
                }}<template v-if="entry.route"> · {{ entry.route }}</template>
                · {{ formatDateTime(entry.dt) }}
              </p>
              <!-- trayecto con escalas: cada vuelo con sus horas y la espera
                   entre ellos (en ámbar si la conexión es justa) -->
              <div v-if="entry.journey.length > 1" class="mt-1 flex flex-col gap-0.5">
                <template v-for="(seg, i) in entry.journey" :key="seg.id">
                  <p class="text-xs text-ink-muted truncate">
                    <span
                      v-if="segTime(seg.departure_dt) || segTime(seg.arrival_dt)"
                      class="tabular-nums font-medium"
                    >
                      {{ segTime(seg.departure_dt) ?? '' }}<span v-if="segTime(seg.departure_dt) && segTime(seg.arrival_dt)" class="opacity-50">–</span>{{ segTime(seg.arrival_dt) ?? '' }}<sup v-if="segTime(seg.arrival_dt) && segPlusDays(seg)" class="text-3xs">+{{ segPlusDays(seg) }}</sup>
                    </span>
                    {{ segmentLabel(seg) }}
                    <span v-if="seg.flight_number" class="font-mono text-2xs text-ink-faint">
                      {{ seg.flight_number }}
                    </span>
                  </p>
                  <p
                    v-if="layoverInfo(entry.journey, i)"
                    class="text-xs truncate"
                    :class="layoverInfo(entry.journey, i)!.short ? 'text-warn-strong' : 'text-ink-faint'"
                    v-tooltip.top="
                      layoverInfo(entry.journey, i)!.short
                        ? $t('itinerary.agenda.shortLayover')
                        : undefined
                    "
                  >
                    <i
                      :class="
                        layoverInfo(entry.journey, i)!.short
                          ? 'mdi mdi-alert-outline'
                          : 'mdi mdi-timer-sand'
                      "
                      class="text-2xs"
                    />
                    {{ $t('bookings.card.layover') }} · {{ layoverInfo(entry.journey, i)!.text }}
                  </p>
                </template>
              </div>
            </div>
            <span v-if="entry.b.confirmation_code" class="text-xs font-mono text-ink-faint">
              {{ entry.b.confirmation_code }}
            </span>
          </div>
        </div>
        <p v-else class="text-sm text-ink-faint">{{ $t('trips.overview.noUpcoming') }}</p>
      </div>

      <div v-if="trip.notes" class="bg-surface rounded-card border border-line p-4">
        <h3 class="text-sm font-semibold text-ink-secondary mb-2">
          {{ $t('trips.overview.notes') }}
        </h3>
        <p class="text-sm text-ink-secondary whitespace-pre-wrap">{{ trip.notes }}</p>
      </div>
    </div>

    <div class="flex flex-col gap-4">
      <div class="bg-surface rounded-card border border-line p-2 h-80">
        <PlaceMap
          :places="places.items"
          :bookings="bookings.items"
          :countryCode="trip.countries[0]"
          :route="route"
        />
      </div>
    </div>
  </div>
</template>
