<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import Button from 'primevue/button'
import { LMap, LTileLayer, LCircleMarker, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import { divIcon, type Icon, type Map as LeafletMap } from 'leaflet'
import WorldChoroplethLayer from './WorldChoroplethLayer.vue'
import WorldCountryCard from './WorldCountryCard.vue'
import WorldRegionLayer from './WorldRegionLayer.vue'
import type { WorldPlace } from '../../api/types'
import { countryName, flagEmoji } from '../../countries'
import { KIND_COLORS, KIND_KEYS, displayName, visitedLabel } from '../../utils/worldGrouping'
import { buildCountryStates, visitedCodes } from '../../utils/worldChoropleth'
import { WHITE } from '../../theme'
import { useCountryCenter } from '../../composables/useCountryCenter'
import { useMapTiles } from '../../composables/useMapTiles'
import { useWorldGeometry, type RegionGeometry } from '../../composables/useWorldGeometry'
import { useWorldMarking } from '../../composables/useWorldMarking'

const props = defineProps<{
  /** entradas que pasan los filtros: son las que se pintan como marcadores */
  places: WorldPlace[]
  /**
   * El diario COMPLETO, sin filtrar. El relleno de países y regiones sale de
   * aquí a propósito: con los filtros puestos, un país ya visitado desaparecía
   * de `places`, el mapa lo pintaba como no visitado y tocarlo lo volvía a dar
   * de alta — dos entradas del mismo país en el diario.
   */
  diary: WorldPlace[]
  showEmptyHint: boolean
}>()

const emit = defineEmits<{ edit: [place: WorldPlace] }>()

const selectedId = defineModel<number | null>('selectedId', { default: null })

const tiles = useMapTiles()
const { centerFor } = useCountryCenter()

const mapRef = ref<InstanceType<typeof LMap> | null>(null)
const zoom = ref(2)
const center = ref<[number, number]>([25, 10])

// --- relleno de países ---
// la geometría se descarga al montar el panel (perezosa: solo en /map) y los
// marcadores se pintan sin esperarla
const { geometry, load: loadGeometry, loadRegions } = useWorldGeometry()
const { pending, markCountry, unmarkCountry, markRegion, unmarkRegion } = useWorldMarking()
const hoveredCode = ref<string | null>(null)
const pickedCode = ref<string | null>(null)

const countryStates = computed(() => {
  const states = buildCountryStates(props.diary)
  // los países en vuelo se pintan ya como visitados
  for (const code of pending.value) {
    if (code.includes('-')) continue // los pendientes con guion son regiones
    if (!states.has(code)) {
      states.set(code, { status: 'visited', placeId: null, year: null, cities: 0, regions: 0 })
    }
  }
  return states
})

const pickedState = computed(() => (pickedCode.value ? countryStates.value.get(pickedCode.value) : null))
const pickedPlace = computed(() => {
  const id = pickedState.value?.placeId
  return id ? (props.diary.find((p) => p.id === id) ?? null) : null
})

/** un país con regiones, ciudades o sitios dentro no se quita (el backend da 409) */
const pickedLocked = computed(
  () => (pickedState.value?.cities ?? 0) + (pickedState.value?.regions ?? 0) > 0,
)

function tooltipFor(code: string): string {
  const state = countryStates.value.get(code)
  const year = state?.year ? ` · ${state.year}` : ''
  return `${flagEmoji(code)} ${countryName(code)}${year}`
}

/** tocar un país lo marca; si ya está marcado, abre su ficha */
function onPick(code: string) {
  const state = countryStates.value.get(code)
  if (state?.status === 'visited') {
    pickedCode.value = code
    selectedId.value = state.placeId
    return
  }
  pickedCode.value = null
  markCountry(code)
}

// --- regiones ---
// A partir de este zoom se pintan las regiones de TODOS los países que asoman
// por la pantalla (no las de uno elegido a dedo: adivinar "cuál miras" fallaba
// en cuanto el centro caía en el mar). Cada país es un fichero de ~10 KB que se
// pide una vez y queda en caché; el tope evita ráfagas al alejarse.
const REGION_ZOOM = 4
const REGION_MAX_COUNTRIES = 8

const regionLayers = shallowRef<{ code: string; geometry: RegionGeometry }[]>([])
const regionHovered = ref<string | null>(null)
/** firma del conjunto ya cargado: sin esto se recargaría en cada movimiento */
let regionKey = ''

/** todas las regiones marcadas, por código ISO 3166-2 (son únicos en el mundo) */
const visitedRegions = computed(() => {
  const codes = new Set<string>()
  for (const place of props.diary) {
    if (place.kind === 'region' && place.region_code) codes.add(place.region_code)
  }
  for (const code of pending.value) if (code.includes('-')) codes.add(code)
  return codes
})

/** países cuyas regiones se están pintando (para esconder su bandera) */
const regionCountries = computed(() => new Set(regionLayers.value.map((entry) => entry.code)))

/**
 * Chips flotantes de los países MARCADOS cuyas regiones se están pintando: son
 * los que han perdido su bandera (robaba el clic) y con el relleno tapado por
 * las regiones se quedaban sin ninguna forma de abrir la ficha. Los NO marcados
 * se quedan fuera a propósito: ahí el toque no abriría nada, daría de alta el
 * país entero de un golpe y sin preguntar.
 */
const regionChips = computed(() =>
  regionLayers.value
    .map((entry) => entry.code)
    .filter((code) => countryStates.value.get(code)?.status === 'visited'),
)

async function syncRegions() {
  const geo = geometry.value
  const map = leafletMap()
  if (!geo || !map) return
  if (map.getZoom() < REGION_ZOOM) {
    regionKey = ''
    regionLayers.value = []
    return
  }
  const view = map.getBounds()
  const codes = geo.countriesIn(
    {
      minLat: view.getSouth(),
      maxLat: view.getNorth(),
      minLon: view.getWest(),
      maxLon: view.getEast(),
    },
    REGION_MAX_COUNTRIES,
  )
  const key = codes.join(',')
  if (key === regionKey) return
  regionKey = key
  try {
    const loaded = await Promise.all(
      codes.map(async (code) => ({ code, geometry: await loadRegions(code) })),
    )
    // el mapa puede haberse movido mientras llegaban: manda la última petición
    if (regionKey !== key) return
    regionLayers.value = loaded.filter(
      (entry): entry is { code: string; geometry: RegionGeometry } => !!entry.geometry,
    )
  } catch {
    // geometría ilegible: se olvida la firma para reintentar al siguiente movimiento
    if (regionKey === key) regionKey = ''
  }
}

// los v-model solo sirven de disparador: `update:center` llega con un LatLng de
// Leaflet, no con la tupla que declara el modelo, así que la vista se le pide
// al mapa
watch([zoom, center], syncRegions)


function onRegionPick(country: string, regionCode: string, name: string, at: [number, number]) {
  const marked = props.diary.find((p) => p.kind === 'region' && p.region_code === regionCode)
  if (marked) unmarkRegion(marked.id, name)
  else markRegion(country, regionCode, name, at)
}

// --- alto: el mapa llega hasta el borde inferior de la ventana ---
// Se mide en vez de usar vh porque encima hay cabecera, título, contadores,
// buscador y filtros, y su alto cambia con el idioma y el ancho. El suelo de
// 500 px evita que en pantallas bajas (o con los filtros abiertos) el mapa
// quede reducido a una franja: ahí se prefiere que la página haga scroll.
const MIN_MAP_HEIGHT = 500

const panelEl = ref<HTMLElement | null>(null)
const mapHeight = ref('68vh')

function measureHeight() {
  const el = panelEl.value
  if (!el) return
  // posición en el DOCUMENTO (no en el viewport): así el alto no baila con el scroll
  const top = el.getBoundingClientRect().top + window.scrollY
  // en móvil hay que dejar sitio a la barra de navegación flotante
  const gap = window.innerWidth < 640 ? 104 : 24
  const next = `${Math.max(MIN_MAP_HEIGHT, window.innerHeight - top - gap)}px`
  if (next === mapHeight.value) return
  mapHeight.value = next
  // el contenedor cambia de tamaño sin que el mapa se entere
  requestAnimationFrame(() => leafletMap()?.invalidateSize())
}

// lo de encima del mapa crece y mengua (abrir filtros, cambiar de idioma) sin
// que haya un evento de resize: se vigila el layout
const layoutObserver = new ResizeObserver(() => measureHeight())

onMounted(() => {
  measureHeight()
  window.addEventListener('resize', measureHeight)
  if (panelEl.value?.parentElement) layoutObserver.observe(panelEl.value.parentElement)
  loadGeometry().then(() => fitAll())
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', measureHeight)
  layoutObserver.disconnect()
})

const markers = computed(() => {
  const list: { place: WorldPlace; pos: [number, number] }[] = []
  for (const place of props.places) {
    // con sus regiones abiertas, la bandera del país sobra y encima roba el
    // clic de la región que tiene debajo (markerPane 600 > overlayPane 400)
    if (place.kind === 'country' && place.country_code && regionCountries.value.has(place.country_code)) continue
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

// panel propio para los rótulos: entre los polígonos (overlayPane, 400) y los
// marcadores (600). Se crea antes de montar la capa, de ahí el flag
const LABELS_PANE = 'tt-labels'
const labelsReady = ref(false)

function onMapReady() {
  const map = leafletMap()
  if (map && !map.getPane(LABELS_PANE)) {
    const pane = map.createPane(LABELS_PANE)
    pane.style.zIndex = '450'
    pane.style.pointerEvents = 'none' // los rótulos no roban clics a los países
  }
  labelsReady.value = true
  fitAll()
}

function fitAll() {
  const map = leafletMap()
  if (!map) return
  // OJO: se le pasan puntos sueltos, NO un LatLngBounds. `useGlobalLeaflet:
  // false` hace que vue-leaflet traiga SU copia de Leaflet, así que un objeto
  // creado con el `latLngBounds` de la app falla el instanceof de fitBounds y
  // Leaflet lo descarta con "Bounds are not valid".
  const points: [number, number][] = markers.value.map((m) => m.pos)
  // los países marcados entran por su TERRITORIO PRINCIPAL: con la caja
  // completa, Francia se llevaría el encuadre a la Polinesia
  const geo = geometry.value
  if (geo) {
    for (const code of visitedCodes(countryStates.value)) {
      const box = geo.boundsOf(code)
      if (box) points.push(box[0], box[1])
    }
  }
  if (!points.length) return
  map.fitBounds(points, { padding: [24, 24], maxZoom: 6 })
}

function flyTo(place: WorldPlace) {
  selectedId.value = place.id
  // pequeño delay: da tiempo a que el mapa exista/redimensione tras cambiar de vista
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
}

function flagIcon(place: WorldPlace, selected: boolean): Icon {
  const code = place.country_code
  const flag = code
    ? `<span style="font-size:${selected ? 30 : 24}px; filter:var(--tt-shadow-flag)">${flagEmoji(code)}</span>`
    : `<i class="mdi mdi-map-marker" style="font-size:${selected ? 30 : 24}px;color:${KIND_COLORS.place};filter:var(--tt-shadow-flag)"></i>`
  // el año de visita acompaña a la bandera (tokens: sigue el tema claro/oscuro)
  const year =
    place.visited_year != null
      ? `<span style="font-size:10px;font-weight:600;line-height:1;padding:2px 6px;` +
        `border-radius:9999px;background:var(--tt-surface);color:var(--tt-ink-secondary);` +
        `border:1px solid var(--tt-line);white-space:nowrap">${place.visited_year}</span>`
      : ''
  return divIcon({
    html: `<span style="display:flex;flex-direction:column;align-items:center;gap:1px">${flag}${year}</span>`,
    className: 'tt-flag-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  }) as unknown as Icon
}

defineExpose({ flyTo, fitAll })
</script>

<template>
  <!-- isolate: la banda de z-index del mapa (paneles Leaflet + overlays) se
       queda dentro y no puede pintar sobre la navegación de la app -->
  <div
    ref="panelEl"
    class="relative isolate rounded-card overflow-hidden border border-line"
    :style="{ height: mapHeight }"
  >
    <LMap
      ref="mapRef"
      v-model:zoom="zoom"
      v-model:center="center"
      :useGlobalLeaflet="false"
      class="w-full h-full"
      @ready="onMapReady"
    >
      <!-- cartografía en dos capas con el relleno EN MEDIO: los rótulos de
           países, regiones y ciudades quedan legibles sobre el verde -->
      <LTileLayer
        :key="tiles.baseUrl.value"
        :url="tiles.baseUrl.value"
        :attribution="tiles.attribution"
        layer-type="base"
        name="Base"
      />
      <!-- los polígonos van al overlayPane (400) y los marcadores al markerPane
           (600): las banderas y los círculos siguen por encima del relleno -->
      <WorldChoroplethLayer
        v-if="geometry"
        :geometry="geometry"
        :states="countryStates"
        :hoveredCode="hoveredCode"
        :label="tooltipFor"
        @hover="(code) => (hoveredCode = code)"
        @pick="onPick"
      />
      <WorldRegionLayer
        v-for="entry in regionLayers"
        :key="entry.code"
        :geometry="entry.geometry"
        :visited="visitedRegions"
        :hoveredCode="regionHovered"
        @hover="(code) => (regionHovered = code)"
        @pick="(code, name, at) => onRegionPick(entry.code, code, name, at)"
      />
      <!-- solo-rótulos, en su propio panel por encima del choropleth -->
      <LTileLayer
        v-if="labelsReady"
        :key="tiles.labelsUrl.value"
        :url="tiles.labelsUrl.value"
        :options="{ pane: LABELS_PANE }"
      />
      <template v-for="{ place, pos } in markers" :key="place.id">
        <!-- la bandera abre la MISMA ficha que el polígono: a zoom bajo tapa a
             los países pequeños y si no, el clic no llegaría nunca al relleno -->
        <LMarker
          v-if="place.kind === 'country'"
          :lat-lng="pos"
          :icon="flagIcon(place, selectedId === place.id)"
          @click="place.country_code && onPick(place.country_code)"
        />
        <LCircleMarker
          v-else
          :lat-lng="pos"
          :radius="selectedId === place.id ? 12 : place.kind === 'city' ? 9 : 7"
          :color="WHITE"
          :weight="2"
          :fillColor="KIND_COLORS[place.kind]"
          :fillOpacity="0.95"
          @click="selectedId = place.id"
        >
          <LPopup>
            <div class="font-medium">{{ place.name }}</div>
            <div class="text-xs text-ink-muted">
              {{ $t(KIND_KEYS[place.kind]) }}
              <template v-if="place.country_code"> · {{ countryName(place.country_code) }}</template>
              <template v-if="visitedLabel(place)"> · {{ visitedLabel(place) }}</template>
            </div>
            <div v-if="place.origin" class="text-xs text-ink-faint">
              {{ $t('world.map.tripOrigin', { origin: place.origin }) }}
            </div>
            <div v-if="place.note" class="text-xs text-ink-muted max-w-52 whitespace-pre-wrap mt-1">
              {{ place.note }}
            </div>
            <button class="text-xs text-info hover:underline mt-1" @click="emit('edit', place)">
              {{ $t('world.map.editNote') }}
            </button>
          </LPopup>
        </LCircleMarker>
      </template>
    </LMap>
    <!-- países con regiones a la vista: arriba a la derecha porque el control
         de zoom ocupa la izquierda y la ficha sale por abajo -->
    <div
      v-if="regionChips.length"
      class="absolute top-2 right-2 z-map-overlay flex flex-wrap justify-end gap-1 max-w-xs"
    >
      <button
        v-for="code in regionChips"
        :key="code"
        type="button"
        class="tt-pop-in bg-surface border border-brand rounded-full shadow-lift px-2 py-1 text-base leading-none"
        :title="countryName(code)"
        :aria-label="countryName(code)"
        @click="onPick(code)"
      >
        {{ flagEmoji(code) }}
      </button>
    </div>

    <!-- pista flotante cuando el diario está vacío -->
    <div
      v-if="showEmptyHint"
      class="absolute bottom-6 left-1/2 -translate-x-1/2 z-map-overlay pointer-events-none"
    >
      <div
        class="bg-white/95 backdrop-blur rounded-card border border-line shadow-lg px-4 py-3 text-center"
      >
        <p class="font-medium text-ink">🌍 {{ $t('world.empty.title') }}</p>
        <p class="text-xs text-ink-muted mt-0.5">
          {{ $t('world.empty.mapHint') }}
        </p>
      </div>
    </div>

    <!-- ficha del país tocado: va sobre el mapa, no en un popup de Leaflet -->
    <WorldCountryCard
      v-if="pickedCode && pickedState"
      :code="pickedCode"
      :state="pickedState"
      :place="pickedPlace"
      :locked="pickedLocked"
      @close="pickedCode = null"
      @edit="pickedPlace && emit('edit', pickedPlace)"
      @remove="pickedPlace && unmarkCountry(pickedCode, pickedPlace.id)"
    />
  </div>
</template>
