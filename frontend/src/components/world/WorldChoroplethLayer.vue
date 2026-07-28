<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'
import { LGeoJson } from '@vue-leaflet/vue-leaflet'
import type { Layer, Path, PathOptions, LeafletMouseEvent } from 'leaflet'
import type { Feature } from 'geojson'
import { useTheme } from '../../composables/useTheme'
import { WORLD_CHOROPLETH } from '../../theme'
import { fillOpacityFor, type CountryState } from '../../utils/worldChoropleth'
import type { CountryFeature, CountryGeometry } from '../../composables/useWorldGeometry'

// Relleno de países del mapa mundial. El estilo NO va por props: vue-leaflet
// reconstruye la capa entera al cambiar `geojson` y recorre los 241 features al
// cambiar `optionsStyle`, así que se guarda cada capa por código y se hace
// setStyle SOLO en los países que cambian.
const props = defineProps<{
  geometry: CountryGeometry
  states: Map<string, CountryState>
  hoveredCode: string | null
  /** etiqueta del tooltip al pasar por encima (bandera, nombre y año) */
  label: (code: string) => string
}>()

const emit = defineEmits<{ pick: [code: string]; hover: [code: string | null] }>()

const { isDark } = useTheme()
const layersByCode = new Map<string, Path[]>()

function styleFor(code: string | null): PathOptions {
  const dark = isDark.value
  if (!code) {
    // territorios sin código ISO: se insinúan, no se pueden marcar
    return {
      fillColor: dark ? WORLD_CHOROPLETH.noDataDark : WORLD_CHOROPLETH.noData,
      fillOpacity: dark ? 0.12 : 0.18,
      color: dark ? WORLD_CHOROPLETH.idleStrokeDark : WORLD_CHOROPLETH.idleStroke,
      weight: 0.4,
      opacity: 0.25,
    }
  }
  const state = props.states.get(code)
  const visited = state?.status === 'visited'
  const hovered = props.hoveredCode === code
  const opacity = fillOpacityFor(state)
  return {
    fillColor: dark ? WORLD_CHOROPLETH.fillDark : WORLD_CHOROPLETH.fill,
    // el hover también se nota en los no visitados: hay que ver qué vas a marcar
    fillOpacity: hovered ? Math.max(opacity + 0.12, 0.16) : opacity,
    color: visited
      ? dark
        ? WORLD_CHOROPLETH.strokeDark
        : WORLD_CHOROPLETH.stroke
      : dark
        ? WORLD_CHOROPLETH.idleStrokeDark
        : WORLD_CHOROPLETH.idleStroke,
    weight: visited ? (hovered ? 2 : 0.9) : hovered ? 1.4 : 0.5,
    opacity: visited ? 0.9 : 0.35,
    // fill true aunque sea transparente: sin él no hay hit-test en el interior
    fill: true,
  }
}

function restyle(code: string) {
  for (const layer of layersByCode.get(code) ?? []) layer.setStyle(styleFor(code))
}

function onEachFeature(feature: Feature, layer: Layer) {
  const code = props.geometry.codeOf(feature as CountryFeature)
  const path = layer as Path
  path.setStyle(styleFor(code))
  if (!code) {
    path.options.interactive = false
    return
  }
  const list = layersByCode.get(code)
  if (list) list.push(path)
  else layersByCode.set(code, [path])

  layer.on({
    click: (event: LeafletMouseEvent) => {
      // sin esto, el clic en el polígono también llega al mapa
      event.originalEvent?.stopPropagation()
      emit('pick', code)
    },
    mouseover: (event: LeafletMouseEvent) => {
      // el tooltip se reconstruye en cada entrada: así sigue al idioma y al
      // estado del país sin tener que re-vincular 241 capas
      layer
        .bindTooltip(props.label(code), { sticky: true, direction: 'top' })
        .openTooltip(event.latlng)
      emit('hover', code)
    },
    mouseout: () => emit('hover', null),
  })
}

// diff incremental: solo se repintan los países cuyo estado ha cambiado
let previous = new Map<string, CountryState>()
watch(
  () => props.states,
  (states) => {
    const codes = new Set([...previous.keys(), ...states.keys()])
    for (const code of codes) {
      const before = previous.get(code)
      const after = states.get(code)
      // `regions` cuenta igual que `cities` en fillOpacityFor: sin compararlo,
      // marcar la 2ª región de un país ya visitado no repintaba nada
      if (
        before?.status !== after?.status ||
        before?.cities !== after?.cities ||
        before?.regions !== after?.regions
      ) {
        restyle(code)
      }
    }
    previous = new Map(states)
  },
  { immediate: true, deep: true },
)

// el hover solo toca dos países (el que entra y el que sale)
watch(
  () => props.hoveredCode,
  (code, old) => {
    if (old) restyle(old)
    if (code) restyle(code)
  },
)

// el tema cambia los dos extremos de la paleta: aquí sí toca repintarlo todo
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
