<script setup lang="ts">
import Button from 'primevue/button'
import Pill from '../ui/Pill.vue'
import type { DayForecast } from '../../api/types'
import { weatherIcon } from '../../utils/weather'

// Cabecera de la tarjeta de un día: fecha, lo que hay que saber de ese día
// (avisos, cama, kilómetros, tiempo) y el botón de añadir. Tonta: recibe todo
// resuelto.
defineProps<{
  title: string
  sub: string
  /** motivos por los que el día no cuadra; vacío = día tranquilo */
  issues: string[]
  issuesTooltip: string
  /** esa noche no hay alojamiento reservado */
  lodgingGap: boolean
  /** "12 km · 1 h 20 min" de traslados propios, o null */
  transfers: string | null
  forecast?: DayForecast | null
}>()
defineEmits<{ add: [] }>()
</script>

<template>
  <div
    class="flex items-center justify-between px-4 py-2.5 bg-surface-muted border-b border-line-subtle"
  >
    <div class="flex items-baseline gap-2 min-w-0">
      <span class="font-semibold text-ink capitalize">{{ title }}</span>
      <span class="text-sm text-ink-faint truncate">{{ sub }}</span>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <Pill v-if="issues.length" color="warn" icon="mdi mdi-alert-outline" v-tooltip.top="issuesTooltip">
        <span class="max-sm:hidden">{{ $t('itinerary.transfers.tight') }}</span>
      </Pill>
      <Pill
        v-if="lodgingGap"
        color="warn"
        icon="mdi mdi-bed-empty"
        v-tooltip.top="$t('trips.lodging.nightGapTooltip')"
      >
        <span class="max-sm:hidden">{{ $t('trips.lodging.nightGap') }}</span>
      </Pill>
      <!-- kilómetros y tiempo de los traslados del día (estimación) -->
      <Pill
        v-if="transfers"
        icon="mdi mdi-map-marker-distance"
        class="hidden sm:inline-flex"
        v-tooltip.top="$t('itinerary.transfers.estimate')"
      >
        <span class="tabular-nums">{{ transfers }}</span>
      </Pill>
      <!-- previsión del alojamiento de la noche (días dentro del horizonte) -->
      <span
        v-if="forecast"
        class="flex items-center gap-1.5 text-xs text-ink-muted whitespace-nowrap"
      >
        <i :class="weatherIcon(forecast.weather_code)" class="text-sm" />
        <span class="tabular-nums">
          {{ Math.round(forecast.t_max) }}° / {{ Math.round(forecast.t_min) }}°
        </span>
        <span
          v-if="(forecast.precip_prob ?? 0) >= 30"
          class="text-info"
          v-tooltip.top="$t('itinerary.agenda.rainProb', { pct: forecast.precip_prob })"
        >
          <i class="mdi mdi-water text-2xs" />{{ forecast.precip_prob }}%
        </span>
      </span>
      <Button
        icon="pi pi-plus"
        text
        size="small"
        severity="secondary"
        v-tooltip.left="$t('itinerary.agenda.addToDay')"
        @click="$emit('add')"
      />
    </div>
  </div>
</template>
