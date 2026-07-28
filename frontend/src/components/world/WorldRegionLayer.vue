<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'
import { LGeoJson } from '@vue-leaflet/vue-leaflet'
import type { Layer, Path, PathOptions, LeafletMouseEvent } from 'leaflet'
import type { Feature } from 'geojson'
import { useTheme } from '../../composables/useTheme'
import { WORLD_CHOROPLETH } from '../../theme'
import type { CountryFeature, RegionGeometry } from '../../composables/useWorldGeometry'

// Regiones de UN país (ISO 3166-2), encima del relleno de países. Mismo truco
// de restyle incremental que WorldChoroplethLayer: se guardan las capas por
// código y solo se repinta la que cambia.
const props = defineProps<{
  geometry: RegionGeometry
  /** códigos ISO 3166-2 ya marcados */
  visited: Set<string>
  hoveredCode: string | null
}>()

const emit = defineEmits<{
  pick: [code: string, name: string]
  hover: [code: string | null]
}>()

const { isDark } = useTheme()
const layersByCode = new Map<string, Path[]>()

function styleFor(code: string): PathOptions {
  const dark = isDark.value
  const visited = props.visited.has(code)
  const hovered = props.hoveredCode === code
  return {
    fillColor: dark ? WORLD_CHOROPLETH.fillDark : WORLD_CHOROPLETH.fill,
    // suave a propósito: los rótulos van encima y hay que poder leerlos
    fillOpacity: visited ? (hovered ? 0.42 : 0.3) : hovered ? 0.12 : 0,
    color: visited
      ? dark
        ? WORLD_CHOROPLETH.strokeDark
        : WORLD_CHOROPLETH.stroke
      : dark
        ? WORLD_CHOROPLETH.regionStrokeDark
        : WORLD_CHOROPLETH.regionStroke,
    // el borde de las NO marcadas tiene que verse sobre el beige de la
    // cartografía, no solo sobre el verde de un país ya visitado
    weight: hovered ? 1.8 : visited ? 1.2 : 0.8,
    opacity: visited ? 0.95 : 0.75,
    dashArray: visited ? undefined : '2 3',
    fill: true,
  }
}

function restyle(code: string) {
  for (const layer of layersByCode.get(code) ?? []) layer.setStyle(styleFor(code))
}

function onEachFeature(feature: Feature, layer: Layer) {
  const code = props.geometry.codeOf(feature as CountryFeature)
  const path = layer as Path
  if (!code) {
    path.options.interactive = false
    return
  }
  path.setStyle(styleFor(code))
  const list = layersByCode.get(code)
  if (list) list.push(path)
  else layersByCode.set(code, [path])

  const name = props.geometry.nameOf(feature as CountryFeature)
  layer.on({
    click: (event: LeafletMouseEvent) => {
      event.originalEvent?.stopPropagation()
      emit('pick', code, name)
    },
    mouseover: (event: LeafletMouseEvent) => {
      layer.bindTooltip(name, { sticky: true, direction: 'top' }).openTooltip(event.latlng)
      emit('hover', code)
    },
    mouseout: () => emit('hover', null),
  })
}

watch(
  () => props.visited,
  (now, before) => {
    const codes = new Set([...(before ?? []), ...now])
    for (const code of codes) {
      if (now.has(code) !== (before?.has(code) ?? false)) restyle(code)
    }
  },
)

watch(
  () => props.hoveredCode,
  (code, old) => {
    if (old) restyle(old)
    if (code) restyle(code)
  },
)

watch(isDark, () => {
  for (const code of layersByCode.keys()) restyle(code)
})

onBeforeUnmount(() => layersByCode.clear())
</script>

<template>
  <LGeoJson
    :geojson="geometry.geojson"
    :options="{ onEachFeature, smoothFactor: 1.5, bubblingMouseEvents: false }"
  />
</template>
