<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import AutoComplete from 'primevue/autocomplete'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import WorldMapPanel from '../components/world/WorldMapPanel.vue'
import WorldCountryList from '../components/world/WorldCountryList.vue'
import WorldPlaceDialog, {
  type WorldPlacePrefill,
} from '../components/world/WorldPlaceDialog.vue'
import { api } from '../api/client'
import type { GeocodeResult, WorldPlace, WorldPlaceKind } from '../api/types'
import { COUNTRY_BY_CODE, COUNTRY_OPTIONS, countryName, flagEmoji } from '../countries'
import { useWorldPlacesStore } from '../stores/worldPlaces'
import { useGeocodeSearch } from '../composables/useGeocode'
import {
  displayName,
  emptyWorldFilters,
  filterWorldPlaces,
  groupByCountry,
  inferCountryCode,
  worldStats,
} from '../utils/worldGrouping'

const store = useWorldPlacesStore()
const confirm = useConfirm()
const toast = useToast()
const { results: geoResults, search: geoSearch } = useGeocodeSearch()

const mapPanel = ref<InstanceType<typeof WorldMapPanel> | null>(null)
const selectedId = ref<number | null>(null)

// vista: mapa o lista (funciona en cualquier tamaño de pantalla)
const viewMode = ref<'map' | 'list'>('map')
const viewOptions = [
  { value: 'map', label: 'Mapa', icon: 'pi pi-map' },
  { value: 'list', label: 'Lista', icon: 'pi pi-list' },
]

// filtros
const filters = reactive(emptyWorldFilters())
const kindFilterOptions = [
  { value: 'all', label: 'Todo' },
  { value: 'country', label: 'Países' },
  { value: 'city', label: 'Ciudades' },
  { value: 'place', label: 'Sitios' },
]
const sourceFilterOptions = [
  { value: 'all', label: 'Cualquier origen' },
  { value: 'auto', label: 'De viajes' },
  { value: 'manual', label: 'Añadidos a mano' },
]

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

const countryFilterOptions = computed(() => {
  const codes = new Set(store.items.map((p) => p.country_code).filter((c): c is string => !!c))
  return [
    { value: 'all', label: 'Todos los países' },
    ...[...codes]
      .map((code) => ({ value: code, label: `${flagEmoji(code)} ${countryName(code)}` }))
      .sort((a, b) => a.label.localeCompare(b.label, 'es')),
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
  return COUNTRY_OPTIONS.filter((o) => !existing.has(o.code))
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
    toast.add({
      severity: 'success',
      summary: `${flagEmoji(code)} ${countryName(code)} añadido`,
      life: 3000,
    })
    // esperar al render para que el mapa ya tenga el marcador nuevo
    nextTick(() => mapPanel.value?.fitAll())
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error', detail: String(err), life: 4000 })
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
  confirm.require({
    message: place.auto
      ? `"${displayName(place)}" viene del viaje "${place.origin}". Se ocultará del mapa y no volverá a aparecer.`
      : `¿Quitar "${displayName(place)}" del mapa?`,
    header: 'Quitar del mapa',
    icon: 'pi pi-exclamation-triangle',
    rejectProps: { label: 'Cancelar', severity: 'secondary', outlined: true },
    acceptProps: { label: 'Quitar', severity: 'danger' },
    accept: () => store.remove(place.id),
  })
}
</script>

<template>
  <div>
    <div class="flex items-center gap-2 mb-1">
      <h1 class="text-2xl font-bold text-slate-800">Mapa</h1>
      <button
        class="text-slate-400 hover:text-slate-600 transition-colors"
        v-tooltip.bottom="
          'El diario de vuestros viajes: países, ciudades y sitios visitados, con notas. Se rellena solo con los viajes terminados, los sitios marcados como visitados y los sitios con gastos — y puedes añadir lo que quieras a mano.'
        "
        aria-label="Información sobre el mapa"
      >
        <i class="pi pi-info-circle" />
      </button>
    </div>

    <!-- estadísticas de diario -->
    <div class="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 text-sm text-slate-500">
      <span>
        🌍 <span class="font-semibold text-slate-700">{{ stats.countries }}</span> países
        <span class="text-slate-400">({{ stats.worldPct }}% del mundo)</span>
      </span>
      <span>🏙 <span class="font-semibold text-slate-700">{{ stats.cities }}</span> ciudades</span>
      <span>
        <i class="pi pi-map-marker text-xs" />
        <span class="font-semibold text-slate-700">{{ stats.places }}</span> sitios
      </span>
      <span>💬 <span class="font-semibold text-slate-700">{{ stats.notes }}</span> notas</span>
      <div class="w-full sm:w-56 h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <div
          class="h-full rounded-full bg-amber-500 transition-all"
          :style="{ width: `${stats.worldPct}%` }"
        />
      </div>
    </div>

    <!-- añadir + vista -->
    <div class="flex flex-wrap items-center gap-2 mb-3">
      <AutoComplete
        v-model="searchValue"
        :suggestions="geoResults"
        optionLabel="display_name"
        placeholder="Buscar ciudad o sitio para añadir…"
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
        placeholder="Marcar país visitado…"
        class="w-full sm:w-56"
        @update:modelValue="addCountry"
      />
      <span class="flex-1" />
      <SelectButton
        v-model="viewMode"
        :options="viewOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
      />
    </div>

    <!-- filtros -->
    <div class="flex flex-wrap items-center gap-2 mb-4">
      <InputText
        v-model="filters.searchText"
        placeholder="Filtrar por nombre, nota o viaje…"
        class="w-full sm:w-64"
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
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-52"
      />
      <Select
        v-model="filters.source"
        :options="sourceFilterOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-48"
      />
    </div>

    <WorldMapPanel
      v-if="viewMode === 'map'"
      ref="mapPanel"
      v-model:selectedId="selectedId"
      :places="filtered"
      :showEmptyHint="!store.loading && !store.items.length"
      @edit="openEdit"
    />

    <WorldCountryList
      v-else
      :groups="groups"
      :selectedId="selectedId"
      :empty="!store.loading && !store.items.length"
      :noMatch="!!store.items.length && !filtered.length"
      @fly-to="flyTo"
      @edit="openEdit"
      @remove="removePlace"
    />

    <WorldPlaceDialog
      v-model:visible="showDialog"
      :place="editing"
      :prefill="prefill"
      @saved="onDialogSaved"
    />
  </div>
</template>
