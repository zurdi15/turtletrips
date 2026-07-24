<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import PlaceMap from '../../components/PlaceMap.vue'
import TabSkeleton from '../../components/TabSkeleton.vue'
import type { Trip } from '../../api/types'
import { BOOKING_TYPE_ICONS, BOOKING_TYPE_LABELS } from '../../constants'
import { useExpensesStore } from '../../stores/expenses'
import { usePlacesStore } from '../../stores/places'
import { useBookingsStore } from '../../stores/bookings'
import { formatDateTime, formatMoney } from '../../composables/useMoney'
import { DAY_MS, daysBetween, daysUntil } from '../../utils/dates'
import { budgetPercent } from '../../utils/expenses'

const props = defineProps<{ trip: Trip }>()
const expenses = useExpensesStore()
const places = usePlacesStore()
const bookings = useBookingsStore()

function loadAll(tripId: number) {
  expenses.load(tripId)
  places.load(tripId)
  bookings.load(tripId)
}
onMounted(() => loadAll(props.trip.id))
watch(() => props.trip.id, loadAll)

const daysToStart = computed(() => daysUntil(props.trip.start_date))

const tripDays = computed(() => {
  if (!props.trip.start_date || !props.trip.end_date) return null
  return daysBetween(props.trip.start_date, props.trip.end_date) + 1
})

const budgetPct = computed(() => budgetPercent(expenses.summary))

const visitedCount = computed(() => places.items.filter((p) => p.visited).length)

const nextBookings = computed(() => {
  const now = Date.now()
  return bookings.items
    .filter((b) => b.start_dt && new Date(b.start_dt).getTime() >= now - DAY_MS)
    .slice(0, 4)
})

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
        <div class="bg-white rounded-xl border border-slate-200 p-4 text-center">
          <p class="text-2xl font-bold text-slate-800">{{ tripDays ?? '—' }}</p>
          <p class="text-xs text-slate-400 mt-1">días de viaje</p>
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-4 text-center">
          <p class="text-2xl font-bold" :class="daysToStart != null ? 'text-sky-600' : 'text-slate-800'">
            {{ daysToStart ?? '—' }}
          </p>
          <p class="text-xs text-slate-400 mt-1">días para salir</p>
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-4 text-center">
          <p class="text-2xl font-bold text-slate-800">{{ visitedCount }}/{{ places.items.length }}</p>
          <p class="text-xs text-slate-400 mt-1">sitios visitados</p>
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-4 text-center">
          <p class="text-2xl font-bold text-slate-800">{{ bookings.items.length }}</p>
          <p class="text-xs text-slate-400 mt-1">reservas</p>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 p-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-slate-600">Presupuesto</h3>
          <router-link :to="{ name: 'trip-expenses', params: { id: trip.id } }">
            <Button label="Ver gastos" text size="small" icon="pi pi-arrow-right" iconPos="right" />
          </router-link>
        </div>
        <div class="flex items-baseline gap-2">
          <span class="text-2xl font-bold text-slate-800">
            {{ formatMoney(expenses.summary?.total_base ?? 0, trip.base_currency) }}
          </span>
          <span v-if="expenses.summary?.budget_amount" class="text-sm text-slate-400">
            de {{ formatMoney(expenses.summary.budget_amount, trip.base_currency) }}
          </span>
        </div>
        <div v-if="budgetPct != null" class="mt-3">
          <div class="h-2.5 rounded-full bg-slate-100 overflow-hidden">
            <div
              class="h-full rounded-full transition-all"
              :class="budgetPct >= 100 ? 'bg-red-500' : budgetPct >= 80 ? 'bg-amber-500' : 'bg-emerald-500'"
              :style="{ width: `${budgetPct}%` }"
            />
          </div>
        </div>
        <p v-else class="text-xs text-slate-400 mt-2">
          Define un presupuesto al editar el viaje para ver el progreso.
        </p>
      </div>

      <div class="bg-white rounded-xl border border-slate-200 p-4">
        <h3 class="text-sm font-semibold text-slate-600 mb-3">Próximas reservas</h3>
        <div v-if="nextBookings.length" class="tt-stagger flex flex-col gap-2">
          <div
            v-for="b in nextBookings"
            :key="b.id"
            class="flex items-center gap-3 p-2 rounded-lg bg-slate-50"
          >
            <i :class="BOOKING_TYPE_ICONS[b.type]" class="text-slate-400" />
            <div class="flex-1 min-w-0">
              <p class="font-medium text-sm text-slate-700 truncate">{{ b.title }}</p>
              <p class="text-xs text-slate-400">
                {{ BOOKING_TYPE_LABELS[b.type] }} · {{ formatDateTime(b.start_dt) }}
              </p>
            </div>
            <span v-if="b.confirmation_code" class="text-xs font-mono text-slate-400">
              {{ b.confirmation_code }}
            </span>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400">Nada próximo en la agenda.</p>
      </div>

      <div v-if="trip.notes" class="bg-white rounded-xl border border-slate-200 p-4">
        <h3 class="text-sm font-semibold text-slate-600 mb-2">Notas</h3>
        <p class="text-sm text-slate-600 whitespace-pre-wrap">{{ trip.notes }}</p>
      </div>
    </div>

    <div class="flex flex-col gap-4">
      <div class="bg-white rounded-xl border border-slate-200 p-2 h-80">
        <PlaceMap
          :places="places.items"
          :bookings="bookings.items"
          :countryCode="trip.countries[0]"
        />
      </div>
      <router-link :to="{ name: 'trip-places', params: { id: trip.id } }" class="no-underline">
        <Button label="Ver todos los sitios" icon="pi pi-map" outlined severity="secondary" fluid />
      </router-link>
    </div>
  </div>
</template>
