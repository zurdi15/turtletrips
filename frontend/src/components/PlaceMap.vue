<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { LMap, LTileLayer, LCircleMarker, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import { divIcon, latLngBounds, type Icon, type Map as LeafletMap } from 'leaflet'
import type { Booking, BookingType, Place } from '../api/types'
import {
  BOOKING_TYPE_LABELS,
  PLACE_CATEGORY_COLORS,
  PLACE_CATEGORY_LABELS,
} from '../constants'
import { useCountryCenter } from '../composables/useCountryCenter'
import { useMapTiles } from '../composables/useMapTiles'
import { formatDate } from '../composables/useMoney'

const props = defineProps<{
  places: Place[]
  bookings?: Booking[]
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
const locatedBookings = computed(
  () => (props.bookings ?? []).filter((b) => b.lat != null && b.lon != null),
)
const countryCenter = computed(() => centerFor(props.countryCode))

const BOOKING_MARKERS: Partial<Record<BookingType, { icon: string; color: string }>> = {
  hotel: { icon: 'mdi mdi-bed', color: '#7c3aed' },
  activity: { icon: 'mdi mdi-ticket-outline', color: '#0ea5e9' },
  car_rental: { icon: 'mdi mdi-car', color: '#64748b' },
}

function bookingIcon(booking: Booking): Icon {
  const marker =
    BOOKING_MARKERS[booking.type] ?? { icon: 'mdi mdi-map-marker', color: '#64748b' }
  return divIcon({
    html:
      `<span style="display:flex;align-items:center;justify-content:center;` +
      `width:26px;height:26px;border-radius:9999px;background:${marker.color};` +
      `color:#fff;box-shadow:0 1px 4px rgb(0 0 0 / .45)">` +
      `<i class="${marker.icon}" style="font-size:15px"></i></span>`,
    className: 'tt-booking-marker',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  }) as unknown as Icon
}

function leafletMap(): LeafletMap | undefined {
  return (mapRef.value as unknown as { leafletObject?: LeafletMap } | null)?.leafletObject
}

function fitAll() {
  const map = leafletMap()
  if (!map) return
  const points: [number, number][] = [
    ...located.value.map((p) => [p.lat!, p.lon!] as [number, number]),
    ...locatedBookings.value.map((b) => [b.lat!, b.lon!] as [number, number]),
  ]
  if (points.length) {
    map.fitBounds(latLngBounds(points).pad(0.2), { maxZoom: 15 })
  } else if (countryCenter.value) {
    // sin sitios localizados: centrar en el país del viaje
    map.setView(countryCenter.value, 5)
  }
}

function onReady() {
  fitAll()
}

watch(
  () => located.value.length + locatedBookings.value.length,
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
    class="w-full h-full rounded-card"
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
        <div class="text-xs text-ink-muted">
          {{ PLACE_CATEGORY_LABELS[place.category] }}
          <span v-if="place.visited"> · ✔ visitado</span>
        </div>
      </LPopup>
    </LCircleMarker>
    <LMarker
      v-for="booking in locatedBookings"
      :key="`booking-${booking.id}`"
      :lat-lng="[booking.lat!, booking.lon!]"
      :icon="bookingIcon(booking)"
    >
      <LPopup>
        <div class="font-medium">{{ booking.title }}</div>
        <div class="text-xs text-ink-muted">
          {{ BOOKING_TYPE_LABELS[booking.type] }}
          <template v-if="booking.start_dt">
            · {{ formatDate(booking.start_dt) }}
            <template v-if="booking.end_dt"> → {{ formatDate(booking.end_dt) }}</template>
          </template>
        </div>
        <div v-if="booking.address" class="text-xs text-ink-faint max-w-52 mt-0.5">
          {{ booking.address }}
        </div>
      </LPopup>
    </LMarker>
  </LMap>
</template>
