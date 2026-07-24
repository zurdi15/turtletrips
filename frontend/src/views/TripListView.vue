<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import ProgressSpinner from 'primevue/progressspinner'
import TripFormDialog from '../components/trips/TripFormDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import FilterToggleButton from '../components/ui/FilterToggleButton.vue'
import TripCard from '../components/trips/TripCard.vue'
import TripFilterBar from '../components/trips/TripFilterBar.vue'
import TripHeroCard from '../components/trips/TripHeroCard.vue'
import { useTripsStore } from '../stores/trips'
import { useCountryImage } from '../composables/useCountryImage'
import { countryLabel, countryName } from '../countries'
import { TRIP_STATUS_LABELS } from '../constants'
import { groupTrips, pickHeroTrip } from '../utils/trips'
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

const groups = computed(() => groupTrips(filtered.value, grouping.value))

const heroTrip = computed<Trip | null>(() => pickHeroTrip(store.trips))

function tripImage(trip: Trip): string | null {
  return trip.cover_url ?? imageFor(trip.countries[0])
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
      <TripHeroCard v-if="heroTrip" :trip="heroTrip" :image="tripImage(heroTrip)" />

      <!-- barra de acciones: nuevo viaje, agrupación y toggle de filtros -->
      <div class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center gap-2">
          <Button
            label="Nuevo viaje"
            icon="pi pi-plus"
            class="w-full sm:w-auto"
            @click="showForm = true"
          />
          <SelectButton
            v-model="grouping"
            :options="groupingOptions"
            optionLabel="label"
            optionValue="value"
            :allowEmpty="false"
            class="flex-1 [&_.p-togglebutton]:flex-1"
          />
          <FilterToggleButton v-model="showFilters" :count="activeFilterCount" />
        </div>

        <TripFilterBar
          v-if="showFilters"
          v-model:search="searchText"
          v-model:status="filterStatus"
          v-model:country="filterCountry"
          :statusOptions="statusOptions"
          :countryOptions="countryOptions"
          :activeCount="activeFilterCount"
          @clear="clearFilters"
        />
      </div>

      <!-- Grupos -->
      <p v-if="!filtered.length" class="text-center text-ink-faint py-10">
        Ningún viaje coincide con los filtros
      </p>
      <section v-for="group in groups" :key="group.key">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-ink-faint mb-3">
          {{ group.title }}
          <span class="font-normal normal-case">· {{ group.trips.length }}</span>
        </h2>
        <div class="tt-stagger grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <TripCard
            v-for="trip in group.trips"
            :key="trip.id"
            :trip="trip"
            :image="tripImage(trip)"
          />
        </div>
      </section>
    </div>

    <TripFormDialog v-model:visible="showForm" />
  </div>
</template>
