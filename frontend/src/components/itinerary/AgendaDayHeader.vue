<script setup lang="ts">
import { computed, ref } from 'vue'
import Button from 'primevue/button'
import Popover from 'primevue/popover'
import Pill from '../ui/Pill.vue'
import ForecastChip from './ForecastChip.vue'
import type { DayForecast } from '../../api/types'

// Cabecera de la tarjeta de un día: fecha y botón de añadir en la primera fila
// y, debajo en móvil (a la derecha en escritorio), lo que hay que saber de ese
// día: tiempo, avisos, cama y kilómetros. Todo junto en una fila, en móvil el
// tiempo se comía la fecha y no se sabía qué día era. Tonta: recibe todo resuelto.
const props = defineProps<{
  title: string
  sub: string
  /** motivos por los que el día no cuadra (overlap|tooLong|tooFar); vacío = día tranquilo */
  issues: string[]
  /** esa noche no hay alojamiento reservado */
  lodgingGap: boolean
  /** "12 km · 1 h 20 min" de traslados propios, o null */
  transfers: string | null
  forecast?: DayForecast | null
  /** el enlace compartido reusa esta cabecera sin el botón de añadir */
  readonly?: boolean
}>()
defineEmits<{ add: [] }>()

const hasInfo = computed(
  () => !!props.forecast || props.issues.length > 0 || props.lodgingGap || !!props.transfers,
)

// los motivos del "día apretado" en un popover: un tooltip no se abre en táctil
const issuesPopover = ref<InstanceType<typeof Popover> | null>(null)
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-x-3 gap-y-1.5 px-4 py-2.5 bg-surface-muted border-b border-line-subtle"
  >
    <!-- el ordinal baja de línea antes que recortarse ("D…") -->
    <div class="flex flex-wrap items-baseline gap-x-2 min-w-0 flex-1">
      <span class="font-semibold text-ink inline-block first-letter:uppercase">{{ title }}</span>
      <span class="text-sm text-ink-faint">{{ sub }}</span>
    </div>
    <div
      v-if="hasInfo"
      class="flex flex-wrap items-center gap-x-2 gap-y-1.5 max-sm:order-last max-sm:basis-full"
    >
      <!-- previsión del alojamiento de la noche (días dentro del horizonte) -->
      <ForecastChip
        v-if="forecast"
        :forecast="forecast"
        class="text-ink-muted"
        v-tooltip.top="$t('itinerary.agenda.forecastTooltip')"
      />
      <button
        v-if="issues.length"
        type="button"
        class="cursor-pointer"
        :aria-label="$t('itinerary.transfers.tight')"
        aria-haspopup="true"
        @click="issuesPopover?.toggle($event)"
      >
        <Pill color="warn" icon="mdi mdi-alert-outline">
          {{ $t('itinerary.transfers.tight') }}
          <i class="pi pi-chevron-down text-3xs opacity-60" />
        </Pill>
      </button>
      <Pill
        v-if="lodgingGap"
        color="warn"
        icon="mdi mdi-bed-empty"
        v-tooltip.top="$t('trips.lodging.nightGapTooltip')"
      >
        {{ $t('trips.lodging.nightGap') }}
      </Pill>
      <!-- kilómetros y tiempo de los traslados del día (estimación) -->
      <Pill
        v-if="transfers"
        icon="mdi mdi-map-marker-distance"
        class="!bg-surface"
        v-tooltip.top="$t('itinerary.transfers.estimate')"
      >
        <span class="tabular-nums">{{ transfers }}</span>
      </Pill>
    </div>
    <Button
      v-if="!readonly"
      icon="pi pi-plus"
      text
      size="small"
      severity="secondary"
      class="shrink-0"
      :aria-label="$t('itinerary.agenda.addToDay')"
      v-tooltip.left="$t('itinerary.agenda.addToDay')"
      @click="$emit('add')"
    />
    <Popover ref="issuesPopover">
      <ul class="flex flex-col gap-2 max-w-xs text-sm text-ink-secondary">
        <li v-for="issue in issues" :key="issue" class="flex items-start gap-2">
          <i class="mdi mdi-alert-outline text-warn-strong mt-0.5" />
          {{ $t(`itinerary.transfers.issues.${issue}`) }}
        </li>
      </ul>
    </Popover>
  </div>
</template>
