<script setup lang="ts">
import PlaceMap from '../PlaceMap.vue'
import type { Booking, Place, TripSummary } from '../../api/types'
import type { RouteStop } from '../../utils/itinerary'
import type { PublicDayRow } from '../../utils/publicAgenda'
import type { PrintOptions, PrintSection } from '../../utils/print'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_KEYS } from '../../constants'
import { countryName, flagEmoji } from '../../countries'
import { formatDate, formatDateTime, formatMoney } from '../../composables/useMoney'

/** cabecera del documento; misma forma venga del viaje o del enlace público */
export interface PrintTrip {
  name: string
  countries: string[]
  start_date: string | null
  end_date: string | null
  notes: string | null
  cover_url: string | null
  travelers: { name: string; color: string | null }[]
}

export interface PrintDay {
  day: string
  title: string
  sub: string
  rows: PublicDayRow[]
}

// Documento TONTO: no conoce stores, ni rutas, ni de dónde salen los datos. La
// misma pieza sirve para /trips/:id/print (con gastos) y /s/:token/print (sin
// ellos): quien decide es `sections`.
defineProps<{
  trip: PrintTrip
  days: PrintDay[]
  places: Place[]
  bookings: Booking[]
  route: RouteStop[]
  summary?: TripSummary | null
  options: PrintOptions
  sections: PrintSection[]
}>()

const TONE_CLASSES: Record<string, string> = {
  info: 'text-info-strong',
  warn: 'text-warn-strong',
  lodging: 'text-lodging-strong',
  plain: 'text-ink',
}

function has(sections: PrintSection[], section: PrintSection) {
  return sections.includes(section)
}
</script>

<template>
  <!-- tt-print-light: dentro de este árbol mandan SIEMPRE los tokens claros,
       también en modo oscuro (el papel no tiene tema) -->
  <article class="tt-print-light bg-surface text-ink">
    <!-- portada -->
    <header class="tt-print-avoid-break">
      <img
        v-if="trip.cover_url"
        :src="trip.cover_url"
        alt=""
        class="w-full h-40 sm:h-56 object-cover rounded-card mb-4"
      />
      <h1 class="text-3xl font-bold text-ink-heading">{{ trip.name }}</h1>
      <p class="mt-1 text-sm text-ink-secondary flex flex-wrap items-center gap-x-3 gap-y-1">
        <span v-if="trip.countries.length">
          <template v-for="(code, idx) in trip.countries" :key="code">
            {{ flagEmoji(code) }} {{ countryName(code) }}<template
              v-if="idx < trip.countries.length - 1"
            >
              ·
            </template>
          </template>
        </span>
        <span v-if="trip.start_date">
          {{ formatDate(trip.start_date) }}
          <template v-if="trip.end_date"> → {{ formatDate(trip.end_date) }}</template>
        </span>
        <span v-if="trip.travelers.length">
          {{ trip.travelers.map((who) => who.name).join(' · ') }}
        </span>
      </p>
      <p
        v-if="options.notes && trip.notes"
        class="mt-3 text-sm text-ink-secondary whitespace-pre-wrap"
      >
        {{ trip.notes }}
      </p>
    </header>

    <!-- itinerario: un salto de página por día para que ninguno quede partido -->
    <section v-if="has(sections, 'itinerary')" class="mt-6">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">
        {{ $t('trips.tabs.itinerary') }}
      </h2>
      <div class="flex flex-col gap-3">
        <div
          v-for="entry in days"
          :key="entry.day"
          class="tt-print-avoid-break border border-line rounded-card overflow-hidden"
        >
          <div
            class="flex items-baseline justify-between gap-2 px-3 py-1.5 bg-surface-muted border-b border-line-subtle"
          >
            <span class="font-semibold text-sm capitalize">{{ entry.title }}</span>
            <span class="text-xs text-ink-faint">{{ entry.sub }}</span>
          </div>
          <div
            v-for="row in entry.rows"
            :key="row.key"
            class="flex items-start gap-2 px-3 py-1.5 border-b border-line-faint last:border-b-0 text-sm"
            :class="TONE_CLASSES[row.tone]"
          >
            <span class="w-4 shrink-0 mt-0.5 text-xs grid place-items-center">
              <i v-if="row.icon" :class="row.icon" />
            </span>
            <span class="w-28 shrink-0 text-xs opacity-80 tabular-nums">{{ row.head }}</span>
            <span class="min-w-0">
              <span class="font-medium">{{ row.title }}</span>
              <span v-if="row.place" class="text-xs opacity-70"> · {{ row.place }}</span>
              <span
                v-if="options.notes && row.note"
                class="block text-xs opacity-70 whitespace-pre-line"
              >
                {{ row.note }}
              </span>
            </span>
          </div>
          <p v-if="!entry.rows.length" class="px-3 py-1.5 text-xs text-ink-disabled">
            {{ $t('share.public.emptyDay') }}
          </p>
        </div>
      </div>
    </section>

    <section v-if="has(sections, 'map')" class="mt-6 tt-print-break">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">
        {{ $t('print.map') }}
      </h2>
      <div class="h-72 border border-line rounded-card overflow-hidden">
        <PlaceMap :places="places" :route="route" :countryCode="trip.countries[0]" />
      </div>
    </section>

    <section v-if="has(sections, 'places')" class="mt-6">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">
        {{ $t('trips.tabs.places') }}
      </h2>
      <ul class="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        <li v-for="place in places" :key="place.id" class="tt-print-avoid-break">
          <span class="font-medium">{{ place.name }}</span>
          <span v-if="place.address" class="block text-xs text-ink-faint">{{ place.address }}</span>
        </li>
      </ul>
    </section>

    <section v-if="has(sections, 'bookings')" class="mt-6 tt-print-break">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">
        {{ $t('trips.tabs.bookings') }}
      </h2>
      <ul class="flex flex-col gap-1.5 text-sm">
        <li
          v-for="booking in bookings"
          :key="booking.id"
          class="tt-print-avoid-break flex items-start gap-2 border border-line rounded-card px-3 py-1.5"
        >
          <i :class="BOOKING_TYPE_ICONS[booking.type]" class="text-ink-faint mt-0.5" />
          <div class="min-w-0">
            <span class="font-medium">{{ booking.title }}</span>
            <span class="block text-xs text-ink-faint">
              {{ $t(BOOKING_TYPE_KEYS[booking.type]) }}
              <template v-if="booking.start_dt"> · {{ formatDateTime(booking.start_dt) }}</template>
              <template v-if="booking.provider"> · {{ booking.provider }}</template>
              <template v-if="booking.confirmation_code">
                · {{ booking.confirmation_code }}
              </template>
            </span>
            <span v-if="booking.origin || booking.destination" class="block text-xs">
              {{ booking.origin ?? '?' }} → {{ booking.destination ?? '?' }}
            </span>
          </div>
        </li>
      </ul>
    </section>

    <section v-if="has(sections, 'expenses') && summary" class="mt-6 tt-print-avoid-break">
      <h2 class="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-2">
        {{ $t('trips.tabs.expenses') }}
      </h2>
      <p class="text-lg font-bold text-ink-heading">
        {{ formatMoney(summary.total_base, summary.base_currency) }}
        <span v-if="summary.budget_amount" class="text-sm font-normal text-ink-faint">
          {{ $t('trips.overview.ofBudget', { amount: formatMoney(summary.budget_amount, summary.base_currency) }) }}
        </span>
      </p>
      <ul class="mt-2 grid grid-cols-2 gap-x-4 text-sm">
        <li
          v-for="row in summary.by_category"
          :key="row.category"
          class="flex justify-between gap-2 border-b border-line-faint py-0.5"
        >
          <span>{{ row.category }}</span>
          <span class="tabular-nums">{{ formatMoney(row.total, summary.base_currency) }}</span>
        </li>
      </ul>
    </section>
  </article>
</template>
