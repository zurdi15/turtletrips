<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import AutoComplete from 'primevue/autocomplete'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { LMap, LTileLayer, LCircleMarker, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import { divIcon, latLngBounds, type Icon, type Map as LeafletMap } from 'leaflet'
import EmptyState from '../components/EmptyState.vue'
import { api } from '../api/client'
import type { GeocodeResult, WorldPlace, WorldPlaceKind } from '../api/types'
import { COUNTRIES, COUNTRY_BY_CODE, COUNTRY_OPTIONS, countryName, flagEmoji } from '../countries'
import { useWorldPlacesStore } from '../stores/worldPlaces'
import { useGeocodeSearch } from '../composables/useGeocode'
import { useCountryCenter } from '../composables/useCountryCenter'
import { useMapTiles } from '../composables/useMapTiles'

const store = useWorldPlacesStore()
const confirm = useConfirm()
const toast = useToast()
const tiles = useMapTiles()
const { centerFor } = useCountryCenter()
const { results: geoResults, search: geoSearch } = useGeocodeSearch()

const mapRef = ref<InstanceType<typeof LMap> | null>(null)
const zoom = ref(2)
const center = ref<[number, number]>([25, 10])

// vista: mapa o lista (funciona en cualquier tamaño de pantalla)
const viewMode = ref<'map' | 'list'>('map')
const viewOptions = [
  { value: 'map', label: 'Mapa', icon: 'pi pi-map' },
  { value: 'list', label: 'Lista', icon: 'pi pi-list' },
]

// filtros
const searchText = ref('')
const filterKind = ref<'all' | WorldPlaceKind>('all')
const filterSource = ref<'all' | 'auto' | 'manual'>('all')
const filterCountry = ref<string>('all')

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
const showDialog = ref(false)
const formName = ref('')
const formKind = ref<WorldPlaceKind>('city')
const formNote = ref('')
const formLat = ref<number | null>(null)
const formLon = ref<number | null>(null)
const formCountry = ref<string | null>(null)

const KIND_LABELS: Record<WorldPlaceKind, string> = {
  country: 'País',
  city: 'Ciudad',
  place: 'Sitio',
}
const KIND_COLORS: Record<WorldPlaceKind, string> = {
  country: '#f59e0b',
  city: '#0ea5e9',
  place: '#e11d48',
}
const kindOptions = [
  { value: 'city', label: 'Ciudad' },
  { value: 'place', label: 'Sitio' },
  { value: 'country', label: 'País' },
]
const dialogCountryOptions = computed(() => [
  { code: null as string | null, label: 'Sin país asignado' },
  ...COUNTRY_OPTIONS.map((o) => ({ code: o.code as string | null, label: o.label })),
])

onMounted(() => store.load().then(fitAll))

const selectedId = ref<number | null>(null)

function displayName(place: WorldPlace): string {
  if (place.kind === 'country' && place.country_code) return countryName(place.country_code)
  return place.name
}

// ---- filtrado (aplica a lista y mapa) ----

const filtered = computed(() =>
  store.items.filter((p) => {
    if (filterKind.value !== 'all' && p.kind !== filterKind.value) return false
    if (filterSource.value === 'auto' && !p.auto) return false
    if (filterSource.value === 'manual' && p.auto) return false
    if (filterCountry.value !== 'all' && p.country_code !== filterCountry.value) return false
    if (searchText.value) {
      const q = searchText.value.toLowerCase()
      if (
        !displayName(p).toLowerCase().includes(q) &&
        !(p.note ?? '').toLowerCase().includes(q) &&
        !(p.origin ?? '').toLowerCase().includes(q)
      )
        return false
    }
    return true
  }),
)

const countryFilterOptions = computed(() => {
  const codes = new Set(store.items.map((p) => p.country_code).filter((c): c is string => !!c))
  return [
    { value: 'all', label: 'Todos los países' },
    ...[...codes]
      .map((code) => ({ value: code, label: `${flagEmoji(code)} ${countryName(code)}` }))
      .sort((a, b) => a.label.localeCompare(b.label, 'es')),
  ]
})

// ---- estadísticas de diario ----

const stats = computed(() => {
  const countries = store.countries.length
  return {
    countries,
    worldPct: Math.round((countries / COUNTRIES.length) * 100),
    cities: store.cities.length,
    places: store.pois.length,
    notes: store.items.filter((p) => p.note).length,
  }
})

// ---- agrupación por país ----

interface CountryGroup {
  code: string | null
  title: string
  flag: string
  entry: WorldPlace | null
  children: WorldPlace[]
}

const groups = computed<CountryGroup[]>(() => {
  const byCode = new Map<string, CountryGroup>()
  const ensure = (code: string | null): CountryGroup => {
    const key = code ?? '__none__'
    let group = byCode.get(key)
    if (!group) {
      group = {
        code,
        title: code ? countryName(code) : 'Sin país asignado',
        flag: code ? flagEmoji(code) : '🌐',
        entry: null,
        children: [],
      }
      byCode.set(key, group)
    }
    return group
  }
  for (const place of filtered.value) {
    if (place.kind === 'country') ensure(place.country_code).entry = place
    else ensure(place.country_code).children.push(place)
  }
  const kindOrder: Record<string, number> = { city: 0, place: 1 }
  for (const group of byCode.values()) {
    group.children.sort(
      (a, b) =>
        (kindOrder[a.kind] ?? 2) - (kindOrder[b.kind] ?? 2) ||
        a.name.localeCompare(b.name, 'es'),
    )
  }
  return [...byCode.values()].sort((a, b) => {
    if (a.code === null) return 1
    if (b.code === null) return -1
    return a.title.localeCompare(b.title, 'es')
  })
})

// ---- mapa ----

const markers = computed(() => {
  const list: { place: WorldPlace; pos: [number, number] }[] = []
  for (const place of filtered.value) {
    let pos: [number, number] | null =
      place.lat != null && place.lon != null ? [place.lat, place.lon] : null
    if (!pos && place.kind === 'country') pos = centerFor(place.country_code)
    if (pos) list.push({ place, pos })
  }
  return list
})

function leafletMap(): LeafletMap | undefined {
  return (mapRef.value as unknown as { leafletObject?: LeafletMap } | null)?.leafletObject
}

function fitAll() {
  const map = leafletMap()
  if (!map || !markers.value.length) return
  const bounds = latLngBounds(markers.value.map((m) => m.pos))
  map.fitBounds(bounds.pad(0.25), { maxZoom: 6 })
}

watch(viewMode, async (mode) => {
  if (mode !== 'map') return
  await nextTick()
  setTimeout(() => {
    leafletMap()?.invalidateSize()
    fitAll()
  }, 60)
})

function flagIcon(code: string | null, selected: boolean): Icon {
  return divIcon({
    html: `<span style="font-size:${selected ? 30 : 24}px; filter: drop-shadow(0 1px 2px rgb(0 0 0 / .4))">${code ? flagEmoji(code) : '📍'}</span>`,
    className: 'tt-flag-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  }) as unknown as Icon
}

function flyTo(place: WorldPlace) {
  selectedId.value = place.id
  viewMode.value = 'map'
  nextTick(() => {
    setTimeout(() => {
      leafletMap()?.invalidateSize()
      const marker = markers.value.find((m) => m.place.id === place.id)
      if (marker) {
        leafletMap()?.flyTo(
          marker.pos,
          place.kind === 'place' ? 11 : place.kind === 'city' ? 8 : 5,
        )
      }
    }, 80)
  })
}

// ---- alta desde el buscador ----

function inferCountryCode(displayNameResult: string): string | null {
  const last = displayNameResult.split(',').pop()?.trim().toLowerCase()
  if (!last) return null
  return COUNTRIES.find((c) => c.es.toLowerCase() === last)?.code ?? null
}

function onGeocodeSelect(event: { value: GeocodeResult }) {
  const r = event.value
  editing.value = null
  formName.value = r.display_name.split(',')[0].trim()
  formKind.value = 'city'
  formNote.value = ''
  formLat.value = r.lat
  formLon.value = r.lon
  formCountry.value = inferCountryCode(r.display_name)
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
    toast.add({ severity: 'success', summary: `${flagEmoji(code)} ${countryName(code)} añadido`, life: 3000 })
    fitAll()
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
  formName.value = displayName(place)
  formKind.value = place.kind
  formNote.value = place.note ?? ''
  formLat.value = place.lat
  formLon.value = place.lon
  formCountry.value = place.country_code
  showDialog.value = true
}

async function saveDialog() {
  if (!formName.value.trim()) return
  const payload = {
    name: formName.value.trim(),
    kind: formKind.value,
    note: formNote.value.trim() || null,
    lat: formLat.value,
    lon: formLon.value,
    country_code: formKind.value === 'country' ? (formCountry.value ?? editing.value?.country_code) : formCountry.value,
  }
  try {
    if (editing.value) await store.update(editing.value.id, payload)
    else {
      await store.create(payload)
      fitAll()
    }
    showDialog.value = false
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Error al guardar', detail: String(err), life: 4000 })
  }
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
      <span>📍 <span class="font-semibold text-slate-700">{{ stats.places }}</span> sitios</span>
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
        v-model="searchText"
        placeholder="Filtrar por nombre, nota o viaje…"
        class="w-full sm:w-64"
      />
      <Select
        v-model="filterKind"
        :options="kindFilterOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[7rem] sm:flex-none sm:w-36"
      />
      <Select
        v-model="filterCountry"
        :options="countryFilterOptions"
        optionLabel="label"
        optionValue="value"
        filter
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-52"
      />
      <Select
        v-model="filterSource"
        :options="sourceFilterOptions"
        optionLabel="label"
        optionValue="value"
        class="flex-1 min-w-[9rem] sm:flex-none sm:w-48"
      />
    </div>

    <!-- MAPA (siempre visible y navegable, con o sin puntos) -->
    <div
      v-if="viewMode === 'map'"
      class="relative h-[68vh] lg:h-[74vh] rounded-xl overflow-hidden border border-slate-200"
    >
      <LMap
        ref="mapRef"
        v-model:zoom="zoom"
        v-model:center="center"
        :useGlobalLeaflet="false"
        class="w-full h-full"
        @ready="fitAll"
      >
        <LTileLayer
          :key="tiles.url.value"
          :url="tiles.url.value"
          :attribution="tiles.attribution"
          layer-type="base"
          name="Base"
        />
        <template v-for="{ place, pos } in markers" :key="place.id">
          <LMarker
            v-if="place.kind === 'country'"
            :lat-lng="pos"
            :icon="flagIcon(place.country_code, selectedId === place.id)"
            @click="selectedId = place.id"
          >
            <LPopup>
              <div class="font-medium">{{ displayName(place) }}</div>
              <div v-if="place.origin" class="text-xs text-slate-400">Viaje: {{ place.origin }}</div>
              <div v-if="place.note" class="text-xs text-slate-500 max-w-52 whitespace-pre-wrap mt-1">
                {{ place.note }}
              </div>
              <button class="text-xs text-sky-600 hover:underline mt-1" @click="openEdit(place)">
                Editar nota
              </button>
            </LPopup>
          </LMarker>
          <LCircleMarker
            v-else
            :lat-lng="pos"
            :radius="selectedId === place.id ? 12 : place.kind === 'city' ? 9 : 7"
            color="#ffffff"
            :weight="2"
            :fillColor="KIND_COLORS[place.kind]"
            :fillOpacity="0.95"
            @click="selectedId = place.id"
          >
            <LPopup>
              <div class="font-medium">{{ place.name }}</div>
              <div class="text-xs text-slate-500">
                {{ KIND_LABELS[place.kind] }}
                <template v-if="place.country_code"> · {{ countryName(place.country_code) }}</template>
              </div>
              <div v-if="place.origin" class="text-xs text-slate-400">Viaje: {{ place.origin }}</div>
              <div v-if="place.note" class="text-xs text-slate-500 max-w-52 whitespace-pre-wrap mt-1">
                {{ place.note }}
              </div>
              <button class="text-xs text-sky-600 hover:underline mt-1" @click="openEdit(place)">
                Editar nota
              </button>
            </LPopup>
          </LCircleMarker>
        </template>
      </LMap>
      <!-- pista flotante cuando el diario está vacío -->
      <div
        v-if="!store.loading && !store.items.length"
        class="absolute bottom-6 left-1/2 -translate-x-1/2 z-[500] pointer-events-none"
      >
        <div
          class="bg-white/95 backdrop-blur rounded-xl border border-slate-200 shadow-lg px-4 py-3 text-center"
        >
          <p class="font-medium text-slate-700">🌍 Tu diario está vacío</p>
          <p class="text-xs text-slate-500 mt-0.5">
            Busca una ciudad, marca un país visitado o termina un viaje y aparecerá solo
          </p>
        </div>
      </div>
    </div>

    <!-- LISTA agrupada por país -->
    <div v-else class="flex flex-col gap-4">
      <EmptyState
        v-if="!store.loading && !store.items.length"
        icon="pi pi-globe"
        title="Tu diario está vacío"
        subtitle="Marca tu primer país, busca una ciudad, o termina un viaje y aparecerá solo"
      />
      <p v-else-if="!filtered.length" class="text-center text-sm text-slate-400 py-10">
        Nada coincide con los filtros
      </p>
      <section
        v-for="group in groups"
        :key="group.code ?? 'none'"
        class="bg-white rounded-xl border border-slate-200 overflow-hidden"
      >
        <div class="px-4 py-3 bg-slate-50 border-b border-slate-100">
          <div class="flex items-center gap-2.5 flex-wrap">
            <span class="text-xl">{{ group.flag }}</span>
            <span class="font-semibold text-slate-800">{{ group.title }}</span>
            <Tag
              v-if="group.entry"
              value="visitado"
              severity="success"
              class="text-xs"
            />
            <span v-if="group.entry?.origin" class="text-xs text-slate-400">
              viaje: {{ group.entry.origin }}
            </span>
            <span class="text-xs text-slate-400">
              {{ group.children.length ? `${group.children.length} lugares` : '' }}
            </span>
            <span class="flex-1" />
            <div v-if="group.entry" class="flex gap-1">
              <Button
                icon="pi pi-map-marker"
                text
                size="small"
                severity="secondary"
                v-tooltip.top="'Ver en el mapa'"
                @click="flyTo(group.entry)"
              />
              <Button icon="pi pi-pencil" text size="small" severity="secondary" @click="openEdit(group.entry)" />
              <Button icon="pi pi-trash" text size="small" severity="danger" @click="removePlace(group.entry)" />
            </div>
          </div>
          <p v-if="group.entry?.note" class="text-sm text-slate-500 mt-1.5 whitespace-pre-wrap">
            {{ group.entry.note }}
          </p>
        </div>
        <ul v-if="group.children.length">
          <li
            v-for="place in group.children"
            :key="place.id"
            class="px-4 py-2.5 border-b border-slate-50 last:border-b-0 hover:bg-slate-50 cursor-pointer group"
            :class="{ 'bg-sky-50': selectedId === place.id }"
            @click="flyTo(place)"
          >
            <div class="flex items-center gap-2.5">
              <span
                class="w-2.5 h-2.5 rounded-full shrink-0"
                :style="{ background: KIND_COLORS[place.kind] }"
                v-tooltip.left="KIND_LABELS[place.kind]"
              />
              <span class="font-medium text-slate-700">{{ place.name }}</span>
              <span v-if="place.origin" class="text-xs text-slate-400">
                viaje: {{ place.origin }}
              </span>
              <span class="flex-1" />
              <div class="flex gap-1 hover-actions">
                <Button icon="pi pi-pencil" text size="small" severity="secondary" @click.stop="openEdit(place)" />
                <Button icon="pi pi-trash" text size="small" severity="danger" @click.stop="removePlace(place)" />
              </div>
            </div>
            <p v-if="place.note" class="text-sm text-slate-400 mt-1 pl-5 whitespace-pre-wrap">
              {{ place.note }}
            </p>
          </li>
        </ul>
      </section>
    </div>

    <!-- diálogo crear/editar -->
    <Dialog
      v-model:visible="showDialog"
      modal
      :header="editing ? 'Editar lugar' : 'Añadir al mapa'"
      class="w-full max-w-md mx-4"
    >
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Nombre *</label>
          <InputText v-model="formName" autofocus />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium">Tipo</label>
            <Select
              v-model="formKind"
              :options="kindOptions"
              optionLabel="label"
              optionValue="value"
            />
          </div>
          <div v-if="formKind !== 'country'" class="flex flex-col gap-1">
            <label class="text-sm font-medium">País</label>
            <Select
              v-model="formCountry"
              :options="dialogCountryOptions"
              optionLabel="label"
              optionValue="code"
              filter
            />
          </div>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-sm font-medium">Nota</label>
          <Textarea
            v-model="formNote"
            rows="3"
            autoResize
            placeholder="Lo que quieras recordar de este lugar…"
          />
        </div>
        <p v-if="editing?.auto" class="text-xs text-slate-400">
          <i class="pi pi-info-circle" /> Añadido automáticamente desde el viaje
          "{{ editing.origin }}".
        </p>
      </div>
      <template #footer>
        <Button label="Cancelar" severity="secondary" text @click="showDialog = false" />
        <Button :label="editing ? 'Guardar' : 'Añadir'" @click="saveDialog" />
      </template>
    </Dialog>
  </div>
</template>
