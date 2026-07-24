<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { LMap, LTileLayer, LCircleMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import { latLngBounds, type Map as LeafletMap } from 'leaflet'
import type { Place } from '../api/types'
import { PLACE_CATEGORY_COLORS, PLACE_CATEGORY_LABELS } from '../constants'
import { useCountryCenter } from '../composables/useCountryCenter'
import { useMapTiles } from '../composables/useMapTiles'

const props = defineProps<{
  places: Place[]
  selectedId?: number | null
  countryCode?: string | null
}>()
const emit = defineEmits<{ select: [id: number] }>()

const { centerFor } = useCountryCenter()
const tiles = useMapTiles()

const mapRef = ref<InstanceType<typeof LMap> | null>(null)
const zoom = ref(2)
const center = ref<[number, number]>([25, 0])

const located = computed(() => props.places.filter((p) => p.lat != null && p.lon != null))
const countryCenter = computed(() => centerFor(props.countryCode))

function leafletMap(): LeafletMap | undefined {
  return (mapRef.value as unknown as { leafletObject?: LeafletMap } | null)?.leafletObject
}

function fitAll() {
  const map = leafletMap()
  if (!map) return
  if (located.value.length) {
    const bounds = latLngBounds(located.value.map((p) => [p.lat!, p.lon!] as [number, number]))
    map.fitBounds(bounds.pad(0.2), { maxZoom: 15 })
  } else if (countryCenter.value) {
    // sin sitios localizados: centrar en el país del viaje
    map.setView(countryCenter.value, 5)
  }
}

function onReady() {
  fitAll()
}

watch(
  () => located.value.length,
  () => fitAll(),
)

// cuando llega (async) el centro del país y no hay sitios, aplicar
watch(countryCenter, (c) => {
  if (c && !located.value.length) fitAll()
})

watch(
  () => props.selectedId,
  (id) => {
    if (id == null) return
    const place = located.value.find((p) => p.id === id)
    const map = leafletMap()
    if (place && map) map.flyTo([place.lat!, place.lon!], Math.max(map.getZoom(), 14))
  },
)

/** Recalcula el tamaño (necesario si el mapa estaba oculto, p. ej. toggle móvil) */
function refresh() {
  const map = leafletMap()
  if (!map) return
  map.invalidateSize()
  fitAll()
}

defineExpose({ refresh })
</script>

<template>
  <LMap
    ref="mapRef"
    v-model:zoom="zoom"
    v-model:center="center"
    :useGlobalLeaflet="false"
    class="w-full h-full rounded-xl"
    @ready="onReady"
  >
    <LTileLayer
      :key="tiles.url.value"
      :url="tiles.url.value"
      :attribution="tiles.attribution"
      layer-type="base"
      name="Base"
    />
    <LCircleMarker
      v-for="place in located"
      :key="place.id"
      :lat-lng="[place.lat!, place.lon!]"
      :radius="place.id === selectedId ? 12 : 9"
      :color="'#ffffff'"
      :weight="2"
      :fillColor="PLACE_CATEGORY_COLORS[place.category]"
      :fillOpacity="place.visited ? 0.35 : 0.95"
      @click="emit('select', place.id)"
    >
      <LPopup>
        <div class="font-medium">{{ place.name }}</div>
        <div class="text-xs text-slate-500">
          {{ PLACE_CATEGORY_LABELS[place.category] }}
          <span v-if="place.visited"> · ✔ visitado</span>
        </div>
      </LPopup>
    </LCircleMarker>
  </LMap>
</template>
