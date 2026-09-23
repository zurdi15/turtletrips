<script setup lang="ts">
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
import ForecastChip from './ForecastChip.vue'
import type { DayForecast, ItineraryItem } from '../../api/types'
import { TRANSFER_MODE_ICONS } from '../../constants'
import { intlLocale } from '../../i18n'
import { fmtDayShort, fmtTime, rangeNights } from '../../utils/itinerary'
import { formatKm, formatMinutes, type Transfer, type TransferMode } from '../../utils/transfers'

// contenido de una fila arrastrable de la agenda; el bucle <draggable> vive en
// el padre (el drag entre días no puede cruzar un boundary de componente)
defineProps<{
  item: ItineraryItem
  tripId: number
  placeName: string | null
  bookingTitle: string | null
  expenseId: number | null
  /** previsión del sitio de ESTA actividad, solo si difiere de la del día
   *  (repetida en cada fila era ruido) */
  forecast?: DayForecast | null
  /** traslado desde la parada anterior: se pinta ENCIMA de la fila */
  transfer?: Transfer | null
  transferMode?: TransferMode
  /** enlace compartido: ni asa, ni acciones, ni enlaces a la app */
  readonly?: boolean
}>()
defineEmits<{ edit: []; remove: [] }>()
</script>

<template>
  <div class="border-b border-line-faint last:border-b-0 hover:bg-surface-hover group">
    <!-- cuánto hay desde la parada anterior (estimado, ver tooltip). El tramo
         que cubre un vuelo o un tren va en azul y SIN duración: la sabe el
         billete, no una estimación a velocidad urbana -->
    <div
      v-if="transfer"
      class="flex items-center gap-1.5 pl-10 pr-4 pt-2 text-2xs"
      :class="
        transfer.covered ? 'text-info' : transfer.longHaul ? 'text-warn-strong' : 'text-ink-faint'
      "
      v-tooltip.top="
        transfer.covered ? $t('itinerary.transfers.covered') : $t('itinerary.transfers.estimate')
      "
    >
      <i class="mdi mdi-arrow-down-thin" />
      <i :class="transfer.covered ? 'mdi mdi-plane-train' : TRANSFER_MODE_ICONS[transferMode ?? 'walk']" />
      <span class="tabular-nums">
        {{ formatKm(transfer.km, intlLocale()) }}
        <template v-if="!transfer.covered"> · {{ formatMinutes(transfer.minutes) }}</template>
      </span>
    </div>
    <div class="flex items-center gap-3 px-4 py-2.5">
      <i
        v-if="!readonly"
        class="pi pi-bars drag-handle cursor-grab text-ink-disabled group-hover:text-ink-faint"
      />
      <div class="flex-1 min-w-0" :class="readonly ? '' : 'ml-1'">
        <!-- hora y tiempo en su propia fila (no columna): sin ellos no se
             reserva espacio, y el título se queda con todo el ancho (con el
             tiempo a la derecha, en móvil quedaba una columna de dos palabras) -->
        <p
          v-if="item.start_time || forecast"
          class="flex flex-wrap items-center gap-x-2.5 text-xs text-ink-faint"
        >
          <span v-if="item.start_time" class="font-mono">
            {{ fmtTime(item.start_time) }}<template v-if="item.end_time">–{{ fmtTime(item.end_time) }}</template>
          </span>
          <ForecastChip v-if="forecast" :forecast="forecast" />
        </p>
        <span class="font-medium text-ink">{{ item.title }}</span>
        <!-- enlaces compactos: solo icono, el detalle vive en el tooltip -->
        <span v-if="readonly && placeName" class="ml-2 text-xs text-ink-faint">{{ placeName }}</span>
        <EntityLink
          v-if="!readonly && item.place_id && placeName"
          type="place"
          :tripId="tripId"
          :targetId="item.place_id"
          :tooltip="$t('itinerary.agenda.placeTooltip', { name: placeName })"
          class="ml-2"
        />
        <EntityLink
          v-if="!readonly && item.booking_id && bookingTitle"
          type="booking"
          :tripId="tripId"
          :targetId="item.booking_id"
          :tooltip="$t('itinerary.agenda.bookingTooltip', { name: bookingTitle })"
          class="ml-2"
        />
        <EntityLink
          v-if="!readonly && item.booking_id && expenseId"
          type="expense"
          :tripId="tripId"
          :targetId="expenseId"
          class="ml-2"
        />
        <!-- la duración multi-día en su propia línea: junto al título quedaba raro en móvil -->
        <div v-if="item.end_day && item.end_day > item.day" class="mt-1">
          <span class="text-xs px-1.5 py-0.5 rounded bg-nature-tint text-nature-strong">
            {{ $t('itinerary.agenda.rangeBadge', { n: rangeNights(item) + 1, date: fmtDayShort(item.end_day) }) }}
          </span>
        </div>
        <p v-if="item.notes" class="text-xs text-ink-faint whitespace-pre-line break-words">{{ item.notes }}</p>
      </div>
      <RowActions v-if="!readonly" @edit="$emit('edit')" @remove="$emit('remove')" />
    </div>
  </div>
</template>
