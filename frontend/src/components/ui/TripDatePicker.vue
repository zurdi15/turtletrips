<script setup lang="ts">
// Primitiva TONTA: el DatePicker de PrimeVue con los días del viaje pintados
// de fondo, para ver de un vistazo dónde cae la fecha que eliges dentro del
// viaje. Todo lo demás (showIcon, dateFormat, showButtonBar…) pasa de largo
// vía $attrs, así que se usa igual que el DatePicker de siempre.
import DatePicker from 'primevue/datepicker'
import { tripSpanClass, type CalendarDay } from '../../utils/tripCalendar'

const props = defineProps<{
  /** fechas del viaje en ISO; sin las dos, se comporta como un DatePicker normal */
  tripStart?: string | null
  tripEnd?: string | null
}>()

const model = defineModel<Date | null>({ default: null })

function dayClass(meta: CalendarDay): string {
  return tripSpanClass(meta, props.tripStart, props.tripEnd)
}
</script>

<template>
  <DatePicker v-model="model" v-bind="$attrs">
    <template #date="{ date }">
      <span class="tt-day-inner" :class="dayClass(date)">{{ date.day }}</span>
    </template>
  </DatePicker>
</template>
