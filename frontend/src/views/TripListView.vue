<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ProgressSpinner from 'primevue/progressspinner'
import ClusterBtn from '../components/ui/ClusterBtn.vue'
import TripFormDialog from '../components/trips/TripFormDialog.vue'
import EmptyState from '../components/EmptyState.vue'
import CollapsePanel from '../components/ui/CollapsePanel.vue'
import FilterToggleButton from '../components/ui/FilterToggleButton.vue'
import TripCard from '../components/trips/TripCard.vue'
import TripFilterBar from '../components/trips/TripFilterBar.vue'
import TripHeroCard from '../components/trips/TripHeroCard.vue'
import { useTripsStore } from '../stores/trips'
import { useCountryImage } from '../composables/useCountryImage'
import { countryName } from '../countries'
import { TRIP_STATUS_KEYS, toSelectOptions } from '../constants'
import { groupTrips, pickHeroTrip } from '../utils/trips'
import type { Trip, TripStatus } from '../api/types'

const { t } = useI18n()
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

const statusOptions = computed(() => [
  { value: 'all', label: t('trips.filters.allStatuses') },
  ...toSelectOptions(TRIP_STATUS_KEYS, t),
])

const countryCodes = computed(() => [...new Set(store.trips.flatMap((t) => t.countries))])

const groupingOptions = computed(
  () =>
    [
      { value: 'year', label: t('trips.grouping.byYear'), icon: 'pi pi-calendar' },
      { value: 'status', label: t('trips.grouping.byStatus'), icon: 'pi pi-flag' },
    ] as const,
)

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
      :title="t('trips.empty.title')"
      :subtitle="t('trips.empty.subtitle')"
    >
      <Button :label="t('trips.actions.createTrip')" icon="pi pi-plus" @click="showForm = true" />
    </EmptyState>

    <div v-else class="flex flex-col gap-6">
      <!-- Hero: próximo viaje -->
      <TripHeroCard v-if="heroTrip" :trip="heroTrip" :image="tripImage(heroTrip)" />

      <!-- barra de acciones: nuevo viaje, agrupación y toggle de filtros -->
      <div class="flex flex-col gap-3">
        <div class="flex flex-wrap items-center gap-2">
          <Button
            :label="t('trips.actions.newTrip')"
            icon="pi pi-plus"
            class="w-full sm:w-auto"
            @click="showForm = true"
          />
          <FilterToggleButton v-model="showFilters" :count="activeFilterCount" />
          <ClusterBtn v-model="grouping" :options="groupingOptions" class="flex-1" />
        </div>

        <!-- -mt-3 anula el gap del padre con el panel cerrado; el pt-3 interno lo repone animado -->
        <CollapsePanel :open="showFilters" class="-mt-3">
          <div class="pt-3">
            <TripFilterBar
              v-model:search="searchText"
              v-model:status="filterStatus"
              v-model:country="filterCountry"
              :statusOptions="statusOptions"
              :countryCodes="countryCodes"
              :activeCount="activeFilterCount"
              @clear="clearFilters"
            />
          </div>
        </CollapsePanel>
      </div>

      <!-- Grupos -->
      <p v-if="!filtered.length" class="text-center text-ink-faint py-10">
        {{ t('trips.filters.noMatch') }}
      </p>
      <section v-for="group in groups" :key="group.key">
        <h2 class="text-sm font-semibold uppercase tracking-wide text-ink-faint mb-3">
          {{ group.titleKey ? t(group.titleKey) : group.title }}
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
