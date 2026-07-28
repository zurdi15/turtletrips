<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import PlaceMap from '../components/PlaceMap.vue'
import TabSkeleton from '../components/TabSkeleton.vue'
import EmptyState from '../components/EmptyState.vue'
import PublicAgendaDay from '../components/share/PublicAgendaDay.vue'
import PublicTripHero from '../components/share/PublicTripHero.vue'
import type { Booking, ItineraryItem, Place } from '../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_KEYS } from '../constants'
import { applyVisitorLocale } from '../i18n'
import { usePublicTrip } from '../composables/usePublicTrip'
import { formatDateTime } from '../composables/useMoney'
import {
  agendaDayLabel,
  agendaDays,
  buildLodgingByDay,
  buildOtherBookingsByDay,
  buildRoute,
  buildTransportsByDay,
} from '../utils/itinerary'
import { buildPublicDay } from '../utils/publicAgenda'

const props = defineProps<{ token: string }>()

const { t } = useI18n()
const { trip, loading, gone, load } = usePublicTrip()

onMounted(() => {
  // el invitado no tiene cuenta ni preferencia guardada: manda su navegador
  applyVisitorLocale()
  load(props.token)
})

// El enlace trae tipos propios (sin dinero, códigos ni notas privadas). Para
// reutilizar las derivaciones de la agenda y el mapa se completan con NULOS los
// campos que no viajan: la lista de abajo es, literalmente, lo que el enlace no
// contiene.
const bookings = computed<Booking[]>(() =>
  (trip.value?.bookings ?? []).map((b) => ({
    ...b,
    trip_id: 0,
    confirmation_code: null,
    flight_number: null,
    cost_amount: null,
    cost_currency: null,
    notes: null,
    paid_by_id: null,
    paid_by_common: false,
  })),
)
const places = computed<Place[]>(() =>
  (trip.value?.places ?? []).map((p) => ({ ...p, trip_id: 0, notes: null, visited: false, priority: 0 })),
)
const items = computed<ItineraryItem[]>(() =>
  (trip.value?.itinerary ?? []).map((i) => ({ ...i, trip_id: 0 })),
)

const placeById = computed(() => new Map(places.value.map((p) => [p.id, p])))
const transportsByDay = computed(() => buildTransportsByDay(bookings.value))
const otherBookingsByDay = computed(() => buildOtherBookingsByDay(bookings.value))
const lodgingByDay = computed(() => buildLodgingByDay(bookings.value))
const itemsByDay = computed(() => {
  const map = new Map<string, ItineraryItem[]>()
  for (const item of items.value) map.set(item.day, [...(map.get(item.day) ?? []), item])
  return map
})

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

const agenda = computed(() =>
  days.value.map((day) => ({
    day,
    ...agendaDayLabel(day, trip.value?.start_date ?? null, t),
    rows: buildPublicDay(
      day,
      itemsByDay.value.get(day) ?? [],
      transportsByDay.value.get(day) ?? [],
      otherBookingsByDay.value.get(day) ?? [],
      lodgingByDay.value.get(day) ?? [],
      placeById.value,
      t,
    ),
  })),
)

const route = computed(() => buildRoute(items.value, placeById.value))
const has = (scope: string) => !!trip.value?.scopes.includes(scope as never)
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-6 sm:py-10 flex flex-col gap-8">
    <TabSkeleton v-if="loading" variant="cards" :rows="3" />

    <EmptyState
      v-else-if="gone || !trip"
      icon="pi pi-link"
      :title="t('share.public.goneTitle')"
      :subtitle="t('share.public.goneSubtitle')"
    />

    <template v-else>
      <PublicTripHero :trip="trip" />

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
            :rows="entry.rows"
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
          <li
            v-for="place in places"
            :key="place.id"
            class="bg-surface rounded-card border border-line px-3 py-2"
          >
            <p class="text-sm font-medium text-ink">{{ place.name }}</p>
            <p v-if="place.address" class="text-xs text-ink-faint truncate">{{ place.address }}</p>
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
              </p>
              <p v-if="booking.origin || booking.destination" class="text-xs text-ink-muted">
                {{ booking.origin ?? '?' }} → {{ booking.destination ?? '?' }}
              </p>
            </div>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>
