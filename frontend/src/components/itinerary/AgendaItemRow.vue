<script setup lang="ts">
import RowActions from '../ui/RowActions.vue'
import EntityLink from '../trip/EntityLink.vue'
import type { ItineraryItem } from '../../api/types'
import { fmtDayShort, fmtTime, rangeNights } from '../../utils/itinerary'

// contenido de una fila arrastrable de la agenda; el bucle <draggable> vive en
// el padre (el drag entre días no puede cruzar un boundary de componente)
defineProps<{
  item: ItineraryItem
  tripId: number
  placeName: string | null
  bookingTitle: string | null
  expenseId: number | null
}>()
defineEmits<{ edit: []; remove: [] }>()
</script>

<template>
  <div
    class="flex items-center gap-3 px-4 py-2.5 border-b border-line-faint last:border-b-0 hover:bg-surface-hover group"
  >
    <i class="pi pi-bars drag-handle cursor-grab text-ink-disabled group-hover:text-ink-faint" />
    <!-- sin horas no se pinta nada; el ancho fijo mantiene la columna alineada -->
    <span class="text-xs sm:text-sm font-mono text-ink-faint w-16 sm:w-24 shrink-0">
      <template v-if="item.start_time">
        {{ fmtTime(item.start_time) }}<template v-if="item.end_time">–{{ fmtTime(item.end_time) }}</template>
      </template>
    </span>
    <div class="flex-1 min-w-0">
      <span class="font-medium text-ink">{{ item.title }}</span>
      <span
        v-if="item.end_day && item.end_day > item.day"
        class="ml-2 text-xs px-1.5 py-0.5 rounded bg-nature-tint text-nature-strong"
      >
        {{ $t('itinerary.agenda.rangeBadge', { n: rangeNights(item) + 1, date: fmtDayShort(item.end_day) }) }}
      </span>
      <!-- enlaces compactos: solo icono, el detalle vive en el tooltip -->
      <EntityLink
        v-if="item.place_id && placeName"
        type="place"
        :tripId="tripId"
        :targetId="item.place_id"
        :tooltip="$t('itinerary.agenda.placeTooltip', { name: placeName })"
        class="ml-2"
      />
      <EntityLink
        v-if="item.booking_id && bookingTitle"
        type="booking"
        :tripId="tripId"
        :targetId="item.booking_id"
        :tooltip="$t('itinerary.agenda.bookingTooltip', { name: bookingTitle })"
        class="ml-2"
      />
      <EntityLink
        v-if="item.booking_id && expenseId"
        type="expense"
        :tripId="tripId"
        :targetId="expenseId"
        class="ml-2"
      />
      <p v-if="item.notes" class="text-xs text-ink-faint whitespace-pre-line break-words">{{ item.notes }}</p>
    </div>
    <RowActions @edit="$emit('edit')" @remove="$emit('remove')" />
  </div>
</template>
