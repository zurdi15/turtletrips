<script setup lang="ts">
import { computed, ref } from 'vue'
import { LMap, LTileLayer, LCircleMarker, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import { divIcon, latLngBounds, type Icon, type Map as LeafletMap } from 'leaflet'
import type { WorldPlace } from '../../api/types'
import { countryName, flagEmoji } from '../../countries'
import { KIND_COLORS, KIND_KEYS, displayName } from '../../utils/worldGrouping'
import { WHITE } from '../../theme'
import { useCountryCenter } from '../../composables/useCountryCenter'
import { useMapTiles } from '../../composables/useMapTiles'

const props = defineProps<{
  places: WorldPlace[]
  showEmptyHint: boolean
}>()

const emit = defineEmits<{ edit: [place: WorldPlace] }>()

const selectedId = defineModel<number | null>('selectedId', { default: null })

const tiles = useMapTiles()
const { centerFor } = useCountryCenter()

const mapRef = ref<InstanceType<typeof LMap> | null>(null)
const zoom = ref(2)
const center = ref<[number, number]>([25, 10])

const markers = computed(() => {
  const list: { place: WorldPlace; pos: [number, number] }[] = []
  for (const place of props.places) {
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
  if (!bounds.isValid()) return
  map.fitBounds(bounds.pad(0.25), { maxZoom: 6 })
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

function flagIcon(code: string | null, selected: boolean): Icon {
  return divIcon({
    html: code
      ? `<span style="font-size:${selected ? 30 : 24}px; filter:var(--tt-shadow-flag)">${flagEmoji(code)}</span>`
      : `<i class="mdi mdi-map-marker" style="font-size:${selected ? 30 : 24}px;color:${KIND_COLORS.place};filter:var(--tt-shadow-flag)"></i>`,
    className: 'tt-flag-marker',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  }) as unknown as Icon
}

defineExpose({ flyTo, fitAll })
</script>

<template>
  <div class="relative h-[68vh] lg:h-[74vh] rounded-card overflow-hidden border border-line">
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
        </LMarker>
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
  </div>
</template>
