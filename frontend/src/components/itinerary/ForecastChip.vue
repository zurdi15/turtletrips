<script setup lang="ts">
import type { DayForecast } from '../../api/types'
import { RAIN_ALERT_PCT, weatherIcon } from '../../utils/weather'

// previsión compacta de la agenda: cielo, máx/mín y la lluvia solo si amenaza.
// La misma en la cabecera del día y en las actividades
defineProps<{ forecast: DayForecast }>()
</script>

<template>
  <span class="inline-flex items-center gap-1.5 text-xs whitespace-nowrap">
    <i :class="weatherIcon(forecast.weather_code)" class="text-sm" />
    <span class="tabular-nums">
      {{ Math.round(forecast.t_max) }}° / {{ Math.round(forecast.t_min) }}°
    </span>
    <span
      v-if="(forecast.precip_prob ?? 0) >= RAIN_ALERT_PCT"
      class="text-info"
      v-tooltip.top="$t('itinerary.agenda.rainProb', { pct: forecast.precip_prob })"
    >
      <i class="mdi mdi-water text-2xs" />{{ forecast.precip_prob }}%
    </span>
  </span>
</template>
