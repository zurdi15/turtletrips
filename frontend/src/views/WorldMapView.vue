<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'
import ClusterBtn from '../components/ui/ClusterBtn.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import CollapsePanel from '../components/ui/CollapsePanel.vue'
import FilterToggleButton from '../components/ui/FilterToggleButton.vue'
import WorldAddBar from '../components/world/WorldAddBar.vue'
import WorldFilterPanel from '../components/world/WorldFilterPanel.vue'
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
import type { GeocodeResult, WorldPlace } from '../api/types'
import { COUNTRY_BY_CODE, countryName, flagEmoji } from '../countries'
import { useWorldPlacesStore } from '../stores/worldPlaces'
import {
  buildTimelineSegments,
  countWorldFilters,
  displayName,
  emptyWorldFilters,
  filterWorldPlaces,
  groupByCountry,
  inferCountryCode,
  sortCountryGroups,
  worldStats,
} from '../utils/worldGrouping'

const { t } = useI18n()
const store = useWorldPlacesStore()
const confirmAction = useConfirmDelete()
const notify = useNotify()

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
// orden cronológico compartido por lista, años y cronología (el mapa no ordena)
const sortDesc = ref(true)
const sortableView = computed(() => viewMode.value !== 'map')

// filtros (colapsados bajo el botón "Filtros", como en el home)
const filters = reactive(emptyWorldFilters())
const showFilters = ref(false)
const activeFilterCount = computed(() => countWorldFilters(filters))

function clearFilters() {
  Object.assign(filters, emptyWorldFilters())
}


// años de visita presentes en el diario, del más reciente al más antiguo
const yearFilterOptions = computed(() => {
  const years = new Set(
    store.items.map((p) => p.visited_year).filter((y): y is number => y != null),
  )
  return [...years].sort((a, b) => b - a).map((y) => ({ value: y, label: String(y) }))
})

// alta
const searchValue = ref<string | GeocodeResult>('')
const addCountryCodes = ref<string[]>([])
const addingCountry = ref(false)

// diálogo
const editing = ref<WorldPlace | null>(null)
const prefill = ref<WorldPlacePrefill | null>(null)
const showDialog = ref(false)

onMounted(() => store.load().then(() => mapPanel.value?.fitAll()))

const filtered = computed(() => filterWorldPlaces(store.items, filters))
const groups = computed(() => sortCountryGroups(groupByCountry(filtered.value), sortDesc.value))
const stats = computed(() => worldStats(store.items))
// la cronología muestra los años con lo que pasa el filtro y marca con un hueco
// lo que se queda fuera (así la línea no miente sobre lo que hubo)
const timelineSegments = computed(() => {
  const segments = buildTimelineSegments(store.items, filtered.value)
  return sortDesc.value ? [...segments].reverse() : segments
})
// países visitados (códigos) para el desglose por continentes de las stats:
// salen del diario YA filtrado, así los filtros también dicen algo aquí
const visitedCountryCodes = computed(() =>
  filtered.value
    .filter((p) => p.kind === 'country')
    .map((p) => p.country_code)
    .filter((code): code is string => !!code),
)

// países presentes en el diario: los únicos que tiene sentido filtrar
const journalCountryCodes = computed(() => [
  ...new Set(store.items.map((p) => p.country_code).filter((c): c is string => !!c)),
])

function flyTo(place: WorldPlace) {
  selectedId.value = place.id
  viewMode.value = 'map'
  nextTick(() => mapPanel.value?.flyTo(place))
}

// ---- alta desde el buscador ----

function onGeocodeSelect(result: GeocodeResult) {
  const r = result
  editing.value = null
  prefill.value = {
    name: r.display_name.split(',')[0].trim(),
    kind: 'city',
    lat: r.lat,
    lon: r.lon,
    country_code: inferCountryCode(r.display_name),
  }
  showDialog.value = true
}

// ---- alta rápida de países ----

// los ya marcados no vuelven a salir en el selector
const markedCountryCodes = computed(() =>
  store.countries.map((c) => c.country_code).filter((c): c is string => !!c),
)

// centro del país para plantar su marcador; es opcional, sin coordenadas la
// entrada vale igual (se busca en serie: throttle de 1 req/s en el backend)
async function countryCenter(code: string): Promise<{ lat: number | null; lon: number | null }> {
  try {
    const query = COUNTRY_BY_CODE.get(code)?.en ?? code
    const results = await api.get<GeocodeResult[]>(`/geocode?q=${encodeURIComponent(query)}`)
    return { lat: results[0]?.lat ?? null, lon: results[0]?.lon ?? null }
  } catch {
    return { lat: null, lon: null }
  }
}

async function addCountries() {
  const codes = [...addCountryCodes.value]
  if (!codes.length) return
  addingCountry.value = true
  try {
    const payloads = []
    for (const code of codes) {
      payloads.push({
        name: countryName(code),
        kind: 'country' as const,
        country_code: code,
        ...(await countryCenter(code)),
      })
    }
    await store.createMany(payloads)
  } catch (err) {
    notify.error(t('world.toast.addError'), err)
  } finally {
    addingCountry.value = false
    // los que ya están en el diario salen del selector; si alguno falló, su
    // chip se queda para reintentarlo
    const marked = new Set(markedCountryCodes.value)
    const added = codes.filter((code) => marked.has(code))
    addCountryCodes.value = codes.filter((code) => !marked.has(code))
    if (added.length === 1) {
      const code = added[0]
      notify.success(
        t('world.toast.countryAdded', { flag: flagEmoji(code), name: countryName(code) }),
      )
    } else if (added.length) {
      notify.success(t('world.toast.countriesAdded', { n: added.length }))
    }
    // esperar al render para que el mapa ya tenga los marcadores nuevos
    if (added.length) nextTick(() => mapPanel.value?.fitAll())
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
      <span v-if="stats.regions">
        <i class="mdi mdi-map-outline mr-1" />
        <span class="font-semibold text-ink">{{ stats.regions }}</span> {{ t('world.stats.regions') }}
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

    <WorldAddBar
      v-model:codes="addCountryCodes"
      v-model:search="searchValue"
      :markedCountryCodes="markedCountryCodes"
      :adding="addingCountry"
      @geocode-select="onGeocodeSelect"
      @add="addCountries"
    />

    <!-- filtros + vista -->
    <div class="flex flex-col gap-3 mb-4">
      <!-- son cuatro vistas: en móvil el cluster se lleva su propia fila a todo
           lo ancho y filtros + orden bajan debajo (juntos no caben) -->
      <div class="flex flex-wrap items-center gap-2">
        <ClusterBtn
          v-model="viewMode"
          :options="viewOptions"
          class="order-1 w-full sm:order-2 sm:w-auto sm:flex-1"
        />
        <FilterToggleButton
          v-model="showFilters"
          :count="activeFilterCount"
          class="order-2 sm:order-1"
        />
        <!-- orden cronológico: de lo más reciente a lo más antiguo o al revés -->
        <Button
          v-if="sortableView"
          class="order-3"
          :icon="sortDesc ? 'pi pi-sort-amount-down' : 'pi pi-sort-amount-up'"
          severity="secondary"
          outlined
          v-tooltip.bottom="sortDesc ? t('world.sort.newestFirst') : t('world.sort.oldestFirst')"
          @click="sortDesc = !sortDesc"
        />
      </div>

      <!-- -mt-3 anula el gap del padre con el panel cerrado; el pt-3 interno lo repone animado -->
      <!-- -mt-3 anula el gap del padre con el panel cerrado; el pt-3 interno lo repone animado -->
      <CollapsePanel :open="showFilters" class="-mt-3">
        <div class="pt-3">
          <WorldFilterPanel
            :filters="filters"
            :journalCountryCodes="journalCountryCodes"
            :yearOptions="yearFilterOptions"
            :activeFilterCount="activeFilterCount"
            @clear="clearFilters"
          />
        </div>
      </CollapsePanel>
    </div>

    <WorldMapPanel
      v-if="viewMode === 'map'"
      ref="mapPanel"
      v-model:selectedId="selectedId"
      :places="filtered"
      :diary="store.items"
      :showEmptyHint="!store.loading && !store.items.length"
      @edit="openEdit"
    />

    <WorldYearStats
      v-else-if="viewMode === 'stats'"
      :countryCodes="visitedCountryCodes"
      :yearsFilter="filters.years"
      :countriesFilter="filters.countries"
      :sortDesc="sortDesc"
    />

    <WorldTimeline
      v-else-if="viewMode === 'timeline'"
      :segments="timelineSegments"
      @fly-to="flyTo"
    />

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
