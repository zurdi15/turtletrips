<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import AutoComplete from 'primevue/autocomplete'
import ClusterBtn from '../components/ui/ClusterBtn.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import CollapsePanel from '../components/ui/CollapsePanel.vue'
import FilterToggleButton from '../components/ui/FilterToggleButton.vue'
import WorldMapPanel from '../components/world/WorldMapPanel.vue'
import WorldCountryList from '../components/world/WorldCountryList.vue'
import WorldTimeline from '../components/world/WorldTimeline.vue'
import WorldYearStats from '../components/world/WorldYearStats.vue'
import WorldPlaceDialog, {
  type WorldPlacePrefill,
} from '../components/world/WorldPlaceDialog.vue'
import { api } from '../api/client'
import { useConfirmDelete } from '../composables/useConfirmDelete'
import { useNotify } from '../composables/useNotify'
import type { GeocodeResult, WorldPlace, WorldPlaceKind } from '../api/types'
import { COUNTRY_BY_CODE, countryName, countryOptions, flagEmoji } from '../countries'
import { intlLocale } from '../i18n'
import { useWorldPlacesStore } from '../stores/worldPlaces'
import { useGeocodeSearch } from '../composables/useGeocode'
import {
  buildTimeline,
  displayName,
  emptyWorldFilters,
  filterWorldPlaces,
  groupByCountry,
  inferCountryCode,
  worldStats,
} from '../utils/worldGrouping'

const { t } = useI18n()
const store = useWorldPlacesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()
const { results: geoResults, search: geoSearch } = useGeocodeSearch()

const mapPanel = ref<InstanceType<typeof WorldMapPanel> | null>(null)
const selectedId = ref<number | null>(null)

// vista: mapa, lista, estadísticas anuales o cronología
const viewMode = ref<'map' | 'list' | 'stats' | 'timeline'>('map')
const viewOptions = computed(
  () =>
    [
      { value: 'map', label: t('world.view.map'), icon: 'pi pi-map' },
      { value: 'list', label: t('world.view.list'), icon: 'pi pi-list' },
      { value: 'stats', label: t('world.view.years'), icon: 'pi pi-chart-bar' },
      { value: 'timeline', label: t('world.view.timeline'), icon: 'pi pi-history' },
    ] as const,
)
// los filtros solo aplican a mapa y lista
const filterableView = computed(() => viewMode.value === 'map' || viewMode.value === 'list')

// filtros (colapsados bajo el botón "Filtros", como en el home)
const filters = reactive(emptyWorldFilters())
const showFilters = ref(false)
const activeFilterCount = computed(
  () =>
    (filters.searchText.trim() ? 1 : 0) +
    (filters.kind !== 'all' ? 1 : 0) +
    (filters.country !== 'all' ? 1 : 0) +
    (filters.source !== 'all' ? 1 : 0) +
    (filters.year !== 'all' ? 1 : 0),
)

function clearFilters() {
  Object.assign(filters, emptyWorldFilters())
}

const kindFilterOptions = computed(() => [
  { value: 'all', label: t('world.filters.all') },
  { value: 'country', label: t('world.filters.countries') },
  { value: 'city', label: t('world.filters.cities') },
  { value: 'place', label: t('world.filters.places') },
])
const sourceFilterOptions = computed(() => [
  { value: 'all', label: t('world.filters.anySource') },
  { value: 'auto', label: t('world.filters.fromTrips') },
  { value: 'manual', label: t('world.filters.manual') },
])

// años de visita presentes en el diario, del más reciente al más antiguo
const yearFilterOptions = computed(() => {
  const years = new Set(
    store.items.map((p) => p.visited_year).filter((y): y is number => y != null),
  )
  return [
    { value: 'all' as 'all' | number, label: t('world.filters.anyYear') },
    ...[...years].sort((a, b) => b - a).map((y) => ({ value: y as 'all' | number, label: String(y) })),
  ]
})

// alta
const searchValue = ref<string | GeocodeResult>('')
const addCountryCode = ref<string | null>(null)
const addingCountry = ref(false)

// diálogo
const editing = ref<WorldPlace | null>(null)
const prefill = ref<WorldPlacePrefill | null>(null)
const showDialog = ref(false)

onMounted(() => store.load().then(() => mapPanel.value?.fitAll()))

const filtered = computed(() => filterWorldPlaces(store.items, filters))
const groups = computed(() => groupByCountry(filtered.value))
const stats = computed(() => worldStats(store.items))
const timeline = computed(() => buildTimeline(store.items))
// países visitados (códigos) para el desglose por continentes de las stats
const visitedCountryCodes = computed(() =>
  store.countries.map((c) => c.country_code).filter((code): code is string => !!code),
)

const countryFilterOptions = computed(() => {
  const codes = new Set(store.items.map((p) => p.country_code).filter((c): c is string => !!c))
  return [
    { value: 'all', label: t('world.filters.allCountries') },
    ...[...codes]
      .map((code) => ({ value: code, label: `${flagEmoji(code)} ${countryName(code)}` }))
      .sort((a, b) => a.label.localeCompare(b.label, intlLocale())),
  ]
})

function flyTo(place: WorldPlace) {
  selectedId.value = place.id
  viewMode.value = 'map'
  nextTick(() => mapPanel.value?.flyTo(place))
}

// ---- alta desde el buscador ----

function onGeocodeSelect(event: { value: GeocodeResult }) {
  const r = event.value
  editing.value = null
  prefill.value = {
    name: r.display_name.split(',')[0].trim(),
    kind: 'city',
    lat: r.lat,
    lon: r.lon,
    country_code: inferCountryCode(r.display_name),
  }
  showDialog.value = true
  searchValue.value = ''
}

// ---- alta rápida de país ----

const countryAddOptions = computed(() => {
  const existing = new Set(store.countries.map((c) => c.country_code))
  return countryOptions().filter((o) => !existing.has(o.code))
})

async function addCountry(code: string | null) {
  if (!code) return
  addingCountry.value = true
  try {
    const query = COUNTRY_BY_CODE.get(code)?.en ?? code
    const results = await api.get<GeocodeResult[]>(`/geocode?q=${encodeURIComponent(query)}`)
    await store.create({
      name: countryName(code),
      kind: 'country',
      country_code: code,
      lat: results[0]?.lat ?? null,
      lon: results[0]?.lon ?? null,
    })
    notify.success(
      t('world.toast.countryAdded', { flag: flagEmoji(code), name: countryName(code) }),
    )
    // esperar al render para que el mapa ya tenga el marcador nuevo
    nextTick(() => mapPanel.value?.fitAll())
  } catch (err) {
    notify.error(t('world.toast.addError'), err)
  } finally {
    addingCountry.value = false
    addCountryCode.value = null
  }
}

// ---- editar / borrar ----

function openEdit(place: WorldPlace) {
  editing.value = place
  prefill.value = null
  showDialog.value = true
}

function onDialogSaved(created: boolean) {
  if (created) nextTick(() => mapPanel.value?.fitAll())
}

function removePlace(place: WorldPlace) {
  confirmAction({
    message: place.auto
      ? t('world.confirmRemove.messageAuto', { name: displayName(place), origin: place.origin })
      : t('world.confirmRemove.messageManual', { name: displayName(place) }),
    header: t('world.confirmRemove.header'),
    acceptLabel: t('world.confirmRemove.accept'),
    accept: () => store.remove(place.id),
  })
}

// ---- selección y borrado en bloque (lista) ----

// países con ciudades/sitios visibles: su entrada queda bloqueada
const lockedCodes = computed(
  () =>
    new Set(
      store.items
        .filter((p) => p.kind !== 'country' && p.country_code)
        .map((p) => p.country_code as string),
    ),
)

const selectedIds = ref<number[]>([])
const bulkWorking = ref(false)

// las entradas pueden desaparecer por otras vías (borrado suelto): podar la selección
watch(
  () => store.items,
  (items) => {
    const ids = new Set(items.map((p) => p.id))
    selectedIds.value = selectedIds.value.filter((id) => ids.has(id))
  },
)

function bulkDelete() {
  const count = selectedIds.value.length
  confirmAction({
    message: t('world.confirmBulk.message', { n: count }),
    header: t('world.confirmBulk.header'),
    acceptLabel: t('world.confirmBulk.accept', { n: count }),
    accept: async () => {
      bulkWorking.value = true
      try {
        await store.removeMany(selectedIds.value)
        notify.success(t('world.toast.bulkDeleted', { n: count }))
        selectedIds.value = []
      } finally {
        bulkWorking.value = false
      }
    },
  })
}
</script>

<template>
  <div>
    <PageHeader
      :title="t('world.title')"
      :info="t('world.info')"
      class="mb-1"
    />

    <!-- estadísticas de diario -->
    <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-sm text-ink-muted">
      <span>
        <i class="mdi mdi-earth mr-1" />
        <span class="font-semibold text-ink">{{ stats.countries }}</span> {{ t('world.stats.countries') }}
        <span class="text-ink-faint">{{ t('world.stats.worldPct', { pct: stats.worldPct }) }}</span>
      </span>
      <span>
        <i class="mdi mdi-city-variant-outline mr-1" />
        <span class="font-semibold text-ink">{{ stats.cities }}</span> {{ t('world.stats.cities') }}
      </span>
      <span>
        <i class="mdi mdi-map-marker mr-1" />
        <span class="font-semibold text-ink">{{ stats.places }}</span> {{ t('world.stats.places') }}
      </span>
    </div>

    <!-- añadir: visible en TODAS las vistas (las stats también se alimentan de aquí) -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <AutoComplete
        v-model="searchValue"
        :suggestions="geoResults"
        optionLabel="display_name"
        :placeholder="t('world.search.placePlaceholder')"
        class="w-full sm:w-80 [&_input]:w-full"
        @complete="(e) => geoSearch(e.query)"
        @item-select="onGeocodeSelect"
      />
      <Select
        v-model="addCountryCode"
        :options="countryAddOptions"
        optionLabel="label"
        optionValue="code"
        filter
        :loading="addingCountry"
        :placeholder="t('world.search.countryPlaceholder')"
        class="w-full sm:w-56"
        @update:modelValue="addCountry"
      />
    </div>

    <!-- filtros + vista -->
    <div class="flex flex-col gap-3 mb-4">
      <div class="flex items-center gap-2">
        <FilterToggleButton v-if="filterableView" v-model="showFilters" :count="activeFilterCount" />
        <ClusterBtn v-model="viewMode" :options="viewOptions" class="flex-1" />
      </div>

      <!-- -mt-3 anula el gap del padre con el panel cerrado; el pt-3 interno lo repone animado -->
      <CollapsePanel :open="showFilters && filterableView" class="-mt-3">
      <div class="pt-3">
      <div
        class="flex flex-wrap items-center gap-2 bg-surface-muted border border-line rounded-card p-3"
      >
        <InputText
          v-model="filters.searchText"
          :placeholder="t('world.filters.searchPlaceholder')"
          class="w-full sm:w-auto sm:flex-1"
        />
        <Select
          v-model="filters.kind"
          :options="kindFilterOptions"
          optionLabel="label"
          optionValue="value"
          class="flex-1 min-w-[7rem] sm:flex-none sm:w-36"
        />
        <Select
          v-model="filters.country"
          :options="countryFilterOptions"
          optionLabel="label"
          optionValue="value"
          filter
          class="flex-1 min-w-menu sm:flex-none sm:w-52"
        />
        <Select
          v-model="filters.source"
          :options="sourceFilterOptions"
          optionLabel="label"
          optionValue="value"
          class="flex-1 min-w-menu sm:flex-none sm:w-48"
        />
        <Select
          v-model="filters.year"
          :options="yearFilterOptions"
          optionLabel="label"
          optionValue="value"
          class="flex-1 min-w-[7rem] sm:flex-none sm:w-36"
        />
        <Button
          v-if="activeFilterCount"
          :label="t('common.actions.clear')"
          icon="pi pi-times"
          text
          severity="secondary"
          size="small"
          @click="clearFilters"
        />
      </div>
      </div>
      </CollapsePanel>
    </div>

    <WorldMapPanel
      v-if="viewMode === 'map'"
      ref="mapPanel"
      v-model:selectedId="selectedId"
      :places="filtered"
      :showEmptyHint="!store.loading && !store.items.length"
      @edit="openEdit"
    />

    <WorldYearStats v-else-if="viewMode === 'stats'" :countryCodes="visitedCountryCodes" />

    <WorldTimeline v-else-if="viewMode === 'timeline'" :years="timeline" @fly-to="flyTo" />

    <template v-else>
      <!-- barra de acciones en bloque: aparece con la primera selección -->
      <div
        v-if="selectedIds.length"
        class="tt-pop-in flex items-center gap-2 bg-info-tint border border-info-edge rounded-card p-3 mb-3"
      >
        <span class="text-sm font-semibold text-info-strong">
          {{ t('world.bulk.selected', { n: selectedIds.length }) }}
        </span>
        <span class="flex-1" />
        <Button
          icon="pi pi-trash"
          :label="t('common.actions.delete')"
          severity="danger"
          outlined
          :loading="bulkWorking"
          class="max-sm:[&_.p-button-label]:hidden"
          @click="bulkDelete"
        />
        <Button
          icon="pi pi-times"
          severity="secondary"
          text
          v-tooltip.bottom="t('world.bulk.clearSelection')"
          @click="selectedIds = []"
        />
      </div>

      <WorldCountryList
        v-model:selectedIds="selectedIds"
        :groups="groups"
        :selectedId="selectedId"
        :empty="!store.loading && !store.items.length"
        :noMatch="!!store.items.length && !filtered.length"
        :lockedCodes="lockedCodes"
        @fly-to="flyTo"
        @edit="openEdit"
        @remove="removePlace"
      />
    </template>

    <WorldPlaceDialog
      v-model:visible="showDialog"
      :place="editing"
      :prefill="prefill"
      @saved="onDialogSaved"
    />
  </div>
</template>
