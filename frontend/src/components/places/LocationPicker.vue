<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { LMap, LTileLayer, LMarker } from '@vue-leaflet/vue-leaflet'
import type { LeafletMouseEvent, Map as LeafletMap, Marker } from 'leaflet'
import { useMapTiles } from '../../composables/useMapTiles'

// Mapa pequeño para fijar una ubicación a mano cuando el buscador no la
// encuentra: un toque (o arrastrar el marcador) escribe lat/lon en el
// formulario. Sin geocoder inverso: la dirección la pone quien la conoce.
const props = defineProps<{
  lat: number | null
  lon: number | null
  /** centro inicial sin coordenadas (p. ej. el país del viaje) */
  fallbackCenter?: [number, number] | null
}>()
const emit = defineEmits<{ pick: [lat: number, lon: number] }>()

const tiles = useMapTiles()
const hasPoint = computed(() => props.lat != null && props.lon != null)

const zoom = ref(hasPoint.value ? 14 : props.fallbackCenter ? 5 : 2)
const center = ref<[number, number]>(
  hasPoint.value ? [props.lat!, props.lon!] : (props.fallbackCenter ?? [20, 0]),
)

function round(n: number): number {
  return Math.round(n * 1e6) / 1e6
}

// último punto que salió de AQUÍ: cuando vuelve por props no hay que recentrar
// (el mapa saltaría a cada toque); si viene de fuera (el buscador), sí
let picked: [number, number] | null = null

function pick(lat: number, lon: number) {
  picked = [round(lat), round(lon)]
  emit('pick', picked[0], picked[1])
}

function onClick(event: LeafletMouseEvent) {
  pick(event.latlng.lat, event.latlng.lng)
}

function onDragEnd(event: { target: Marker }) {
  const pos = event.target.getLatLng()
  pick(pos.lat, pos.lng)
}

watch(
  () => [props.lat, props.lon] as const,
  ([lat, lon]) => {
    if (lat == null || lon == null) return
    if (picked && picked[0] === lat && picked[1] === lon) return
    center.value = [lat, lon]
    zoom.value = Math.max(zoom.value, 14)
  },
)

function onReady(map: LeafletMap) {
  // dentro de un diálogo el contenedor se mide antes de estar visible del
  // todo: sin esto el mapa pinta un cuarto de tile y el resto gris
  setTimeout(() => map.invalidateSize(), 150)
}
</script>

<template>
  <div class="h-56 rounded-card overflow-hidden border border-line isolate">
    <LMap
      v-model:zoom="zoom"
      v-model:center="center"
      :useGlobalLeaflet="false"
      class="w-full h-full"
      @ready="onReady"
      @click="onClick"
    >
      <LTileLayer
        :key="tiles.url.value"
        :url="tiles.url.value"
        :attribution="tiles.attribution"
        layer-type="base"
        name="Base"
      />
      <LMarker v-if="hasPoint" :lat-lng="[lat!, lon!]" draggable @dragend="onDragEnd" />
    </LMap>
  </div>
</template>
