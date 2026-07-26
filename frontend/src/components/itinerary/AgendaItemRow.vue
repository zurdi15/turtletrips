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
    <div class="flex-1 min-w-0 ml-1">
      <!-- la hora en su propia fila (no columna): sin ella no se reserva espacio -->
      <p v-if="item.start_time" class="text-xs font-mono text-ink-faint">
        {{ fmtTime(item.start_time) }}<template v-if="item.end_time">–{{ fmtTime(item.end_time) }}</template>
      </p>
      <span class="font-medium text-ink">{{ item.title }}</span>
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
      <!-- la duración multi-día en su propia línea: junto al título quedaba raro en móvil -->
      <div v-if="item.end_day && item.end_day > item.day" class="mt-1">
        <span class="text-xs px-1.5 py-0.5 rounded bg-nature-tint text-nature-strong">
          {{ $t('itinerary.agenda.rangeBadge', { n: rangeNights(item) + 1, date: fmtDayShort(item.end_day) }) }}
        </span>
      </div>
      <p v-if="item.notes" class="text-xs text-ink-faint whitespace-pre-line break-words">{{ item.notes }}</p>
    </div>
    <RowActions @edit="$emit('edit')" @remove="$emit('remove')" />
  </div>
</template>
