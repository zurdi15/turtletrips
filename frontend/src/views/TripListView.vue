<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import ProgressSpinner from 'primevue/progressspinner'
import StatusTag from '../components/StatusTag.vue'
import TripFormDialog from '../components/TripFormDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import { useTripsStore } from '../stores/trips'
import { useCountryImage } from '../composables/useCountryImage'
import { formatDate, parseIsoDate } from '../composables/useMoney'
import { countryLabel, countryName, flagEmoji } from '../countries'
import { TRIP_STATUS_LABELS } from '../constants'
import type { Trip, TripStatus } from '../api/types'

const store = useTripsStore()
const { imageFor } = useCountryImage()
const showForm = ref(false)

const searchText = ref('')
// 'all' como centinela: PrimeVue muestra el placeholder (vacío) si el valor es null
const filterStatus = ref<TripStatus | 'all'>('all')
const filterCountry = ref<string>('all')
const grouping = ref<'year' | 'status'>('year')
const showFilters = ref(false)

const activeFilterCount = computed(
  () =>
    (searchText.value.trim() ? 1 : 0) +
    (filterStatus.value !== 'all' ? 1 : 0) +
    (filterCountry.value !== 'all' ? 1 : 0),
)

function clearFilters() {
  searchText.value = ''
  filterStatus.value = 'all'
  filterCountry.value = 'all'
}

onMounted(() => store.loadTrips())

const statusOptions = [
  { value: 'all', label: 'Todos los estados' },
  ...Object.entries(TRIP_STATUS_LABELS).map(([value, label]) => ({ value, label })),
]

const countryOptions = computed(() => {
  const codes = new Set(store.trips.flatMap((t) => t.countries))
  return [
    { value: 'all', label: 'Todos los países' },
    ...[...codes]
      .map((code) => ({ value: code, label: countryLabel(code) }))
      .sort((a, b) => a.label.localeCompare(b.label, 'es')),
  ]
})

const groupingOptions = [
  { value: 'year', label: 'Por año' },
  { value: 'status', label: 'Por estado' },
]

const filtered = computed(() =>
  store.trips.filter((t) => {
    if (filterStatus.value !== 'all' && t.status !== filterStatus.value) return false
    if (filterCountry.value !== 'all' && !t.countries.includes(filterCountry.value)) return false
    if (searchText.value) {
      const q = searchText.value.toLowerCase()
      const inName = t.name.toLowerCase().includes(q)
      const inCountry = t.countries.some((c) => countryName(c).toLowerCase().includes(q))
      if (!inName && !inCountry) return false
    }
    return true
  }),
)

// orden por fecha de mayor a menor (los próximos antes que los terminados)
function byDateDesc(trips: Trip[]): Trip[] {
  return [...trips].sort((a, b) => {
    if (!a.start_date && !b.start_date) return b.id - a.id
    if (!a.start_date) return 1
    if (!b.start_date) return -1
    return b.start_date.localeCompare(a.start_date)
  })
}

const STATUS_ORDER: TripStatus[] = ['ongoing', 'upcoming', 'planning', 'done']

const groups = computed<{ key: string; title: string; trips: Trip[] }[]>(() => {
  if (grouping.value === 'status') {
    return STATUS_ORDER.filter((s) => filtered.value.some((t) => t.status === s)).map(
      (status) => ({
        key: status,
        title: TRIP_STATUS_LABELS[status],
        trips: byDateDesc(filtered.value.filter((t) => t.status === status)),
      }),
    )
  }
  const byYear = new Map<string, Trip[]>()
  for (const trip of filtered.value) {
    const year = trip.start_date ? trip.start_date.slice(0, 4) : 'Sin fecha'
    byYear.set(year, [...(byYear.get(year) ?? []), trip])
  }
  return [...byYear.entries()]
    .sort((a, b) => {
      if (a[0] === 'Sin fecha') return 1
      if (b[0] === 'Sin fecha') return -1
      return b[0].localeCompare(a[0]) // años recientes primero
    })
    .map(([year, trips]) => ({ key: year, title: year, trips: byDateDesc(trips) }))
})

// hero: viaje en curso, o el próximo MÁS CERCANO en fecha
const heroTrip = computed<Trip | null>(() => {
  const ongoing = store.trips.filter((t) => t.status === 'ongoing')
  if (ongoing.length) return ongoing[0]
  const upcoming = store.trips
    .filter((t) => t.status === 'upcoming' && t.start_date)
    .sort((a, b) => a.start_date!.localeCompare(b.start_date!))
  return upcoming[0] ?? null
})

function tripImage(trip: Trip): string | null {
  return trip.cover_url ?? imageFor(trip.countries[0])
}

function daysUntil(trip: Trip): number | null {
  if (!trip.start_date) return null
  const diff = Math.ceil(
    (parseIsoDate(trip.start_date).getTime() - new Date().setHours(0, 0, 0, 0)) / 86400000,
  )
  return diff > 0 ? diff : null
}

function dateRange(trip: Trip): string {
  if (!trip.start_date) return 'Sin fechas'
  let s = formatDate(trip.start_date)
  if (trip.end_date) s += ` → ${formatDate(trip.end_date)}`
  return s
}
</script>

<template>
  <div>
    <div v-if="store.loading" class="flex justify-center py-20">
      <ProgressSpinner style="width: 40px" />
    </div>

    <EmptyState
      v-else-if="!store.trips.length"
      icon="pi pi-compass"
      title="Todavía no hay viajes"
      subtitle="Crea tu primer viaje para empezar a planificar"
    >
      <Button label="Crear viaje" icon="pi pi-plus" @click="showForm = true" />
    </EmptyState>

    <div v-else class="flex flex-col gap-6">
      <!-- Hero: próximo viaje -->
      <router-link
        v-if="heroTrip"
        :to="`/trips/${heroTrip.id}/overview`"
        class="no-underline block"
      >
        <div class="relative rounded-2xl overflow-hidden bg-slate-800 group">
          <!-- ajustada a los laterales (sin zoom): ancho completo y alto según la imagen -->
          <img
            v-if="tripImage(heroTrip)"
            :src="tripImage(heroTrip)!"
            class="block w-full h-auto min-h-40 max-h-[26rem] object-cover group-hover:scale-105 transition-transform duration-700"
            alt=""
          />
          <div v-else class="h-56 bg-gradient-to-br from-sky-700 to-indigo-900" />
          <div
            class="absolute inset-0 bg-gradient-to-t from-slate-900/85 via-slate-900/20 to-transparent"
          />
          <div class="absolute bottom-0 left-0 right-0 p-4 sm:p-6 text-white">
            <div class="flex items-end justify-between gap-3 sm:gap-4 flex-wrap">
              <div class="min-w-0">
                <p class="text-xs font-semibold uppercase tracking-widest text-white/70 mb-1">
                  <template v-if="heroTrip.status === 'ongoing'">
                    <i class="mdi mdi-airplane text-xs" /> En curso
                  </template>
                  <template v-else>Próximo viaje</template>
                </p>
                <h2 class="text-xl sm:text-3xl font-bold flex items-center gap-2 sm:gap-3 flex-wrap">
                  {{ heroTrip.name }}
                  <span class="text-lg sm:text-2xl">
                    {{ heroTrip.countries.map(flagEmoji).join(' ') }}
                  </span>
                </h2>
                <p class="text-white/80 mt-1 text-xs sm:text-sm">{{ dateRange(heroTrip) }}</p>
              </div>
              <div
                v-if="daysUntil(heroTrip)"
                class="text-center bg-white/15 backdrop-blur rounded-xl px-3 py-2 sm:px-5 sm:py-3"
              >
                <p class="text-xl sm:text-3xl font-bold leading-none">{{ daysUntil(heroTrip) }}</p>
                <p class="text-xs text-white/80 mt-1">días para salir</p>
              </div>
            </div>
          </div>
        </div>
      </router-link>

      <!-- barra de acciones: nuevo viaje, agrupación y toggle de filtros -->
      <div class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center gap-2">
          <Button
            label="Nuevo viaje"
            icon="pi pi-plus"
            class="w-full sm:w-auto"
            @click="showForm = true"
          />
          <span class="flex-1" />
          <SelectButton
            v-model="grouping"
            :options="groupingOptions"
            optionLabel="label"
            optionValue="value"
            :allowEmpty="false"
          />
          <Button
            label="Filtros"
            :icon="showFilters ? 'pi pi-chevron-up' : 'pi pi-sliders-h'"
            severity="secondary"
            :outlined="!showFilters && !activeFilterCount"
            :badge="activeFilterCount ? String(activeFilterCount) : undefined"
            @click="showFilters = !showFilters"
          />
        </div>

        <!-- controles de búsqueda y filtrado (colapsados por defecto);
             en móvil el buscador ocupa su propia línea, en desktop todo en una fila -->
        <div
          v-if="showFilters"
          class="flex flex-wrap items-center gap-2 bg-slate-100 border border-slate-200 rounded-xl p-3"
        >
          <InputText
            v-model="searchText"
            placeholder="Buscar viaje o país…"
            class="w-full sm:w-auto sm:flex-1"
          />
          <Select
            v-model="filterStatus"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            class="flex-1 min-w-[8rem] sm:flex-none sm:w-44"
          />
          <Select
            v-model="filterCountry"
            :options="countryOptions"
            optionLabel="label"
            optionValue="value"
            filter
            class="flex-1 min-w-[8rem] sm:flex-none sm:w-48"
          />
          <Button
            v-if="activeFilterCount"
            label="Limpiar"
            icon="pi pi-times"
            text
            severity="secondary"
            size="small"
            @click="clearFilters"
          />
        </div>
      </div>

      <!-- Grupos -->
      <p v-if="!filtered.length" class="text-center text-slate-400 py-10">
        Ningún viaje coincide con los filtros
      </p>
      <section v-for="group in groups" :key="group.key">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-slate-400 mb-3">
          {{ group.title }}
          <span class="font-normal normal-case">· {{ group.trips.length }}</span>
        </h2>
        <div class="tt-stagger grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <router-link
            v-for="trip in group.trips"
            :key="trip.id"
            :to="`/trips/${trip.id}/overview`"
            class="no-underline"
          >
            <div
              class="tt-lift bg-white rounded-xl border border-slate-200 overflow-hidden h-full group"
            >
              <div class="relative h-32 bg-slate-200 overflow-hidden">
                <img
                  v-if="tripImage(trip)"
                  :src="tripImage(trip)!"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  alt=""
                  loading="lazy"
                />
                <div
                  v-else
                  class="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-sky-100 to-indigo-100"
                >
                  <template v-if="trip.countries.length">
                    {{ trip.countries.map(flagEmoji).join(' ') }}
                  </template>
                  <i v-else class="mdi mdi-bag-suitcase-outline text-slate-400" />
                </div>
                <div class="absolute top-2 right-2">
                  <StatusTag :status="trip.status" />
                </div>
              </div>
              <div class="p-3.5">
                <h3 class="font-semibold text-slate-800 flex items-center gap-2">
                  {{ trip.name }}
                  <span class="text-sm">{{ trip.countries.map(flagEmoji).join(' ') }}</span>
                  <span
                    v-if="trip.debts_settled"
                    class="tt-pop-in inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700"
                    v-tooltip.top="'Deudas saldadas entre viajeros'"
                  >
                    <i class="pi pi-check-circle text-[10px]" />
                    Saldado
                  </span>
                </h3>
                <p class="text-sm text-slate-500 mt-1 flex items-center gap-1.5">
                  <i class="pi pi-calendar text-xs" /> {{ dateRange(trip) }}
                </p>
                <p
                  v-if="trip.travelers.length"
                  class="text-xs text-slate-400 mt-1.5 flex items-center gap-1"
                >
                  <i class="pi pi-users" /> {{ trip.travelers.map((t) => t.name).join(', ') }}
                </p>
              </div>
            </div>
          </router-link>
        </div>
      </section>
    </div>

    <TripFormDialog v-model:visible="showForm" />
  </div>
</template>
