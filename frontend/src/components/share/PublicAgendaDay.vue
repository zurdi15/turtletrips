<script setup lang="ts">
import AgendaBookingSection, { type AgendaRow } from '../itinerary/AgendaBookingSection.vue'
import AgendaDayHeader from '../itinerary/AgendaDayHeader.vue'
import AgendaItemRow from '../itinerary/AgendaItemRow.vue'
import type { DayForecast, ItineraryItem, Place } from '../../api/types'
import type { Transfer, TransferMode } from '../../utils/transfers'

// Tarjeta de un día del viaje compartido. Monta LAS MISMAS piezas que la agenda
// de la app (cabecera con tiempo y avisos, bandas de transporte/reservas/cama y
// filas de actividad) en su modo solo-lectura: así el enlace es un calco y no
// una segunda implementación que se queda atrás.
defineProps<{
  title: string
  sub: string
  issues: string[]
  lodgingGap: boolean
  transfers: string | null
  forecast: DayForecast | null | undefined
  transportRows: AgendaRow[]
  otherRows: AgendaRow[]
  lodgingRows: AgendaRow[]
  items: ItineraryItem[]
  /** actividades de varios días que vienen de atrás ("sigue …") */
  continuations: ItineraryItem[]
  placeById: Map<number, Place>
  itemForecast: (item: ItineraryItem) => DayForecast | null | undefined
  transferOf: (item: ItineraryItem) => Transfer | null
  transferMode: TransferMode
  emptyLabel: string
}>()
</script>

<template>
  <div class="bg-surface rounded-card border border-line overflow-hidden">
    <AgendaDayHeader
      :title="title"
      :sub="sub"
      :issues="issues"
      :lodgingGap="lodgingGap"
      :transfers="transfers"
      :forecast="forecast"
      readonly
    />

    <AgendaBookingSection
      v-if="transportRows.length"
      tone="info"
      icon="mdi mdi-plane-train"
      :title="$t('itinerary.agenda.transport')"
      :tripId="0"
      :rows="transportRows"
      readonly
    />
    <AgendaBookingSection
      v-if="otherRows.length"
      tone="warn"
      icon="pi pi-ticket"
      :title="$t('itinerary.agenda.bookings')"
      :tripId="0"
      :rows="otherRows"
      readonly
    />

    <AgendaItemRow
      v-for="item in items"
      :key="item.id"
      :item="item"
      :tripId="0"
      :placeName="item.place_id != null ? (placeById.get(item.place_id)?.name ?? null) : null"
      :bookingTitle="null"
      :expenseId="null"
      :forecast="itemForecast(item)"
      :transfer="transferOf(item)"
      :transferMode="transferMode"
      readonly
    />

    <!-- misma fila "sigue" que la agenda de la app, sin el clic para editar -->
    <div
      v-for="cont in continuations"
      :key="`cont-${cont.id}`"
      class="flex items-center gap-3 px-4 py-1.5 border-b border-line-faint last:border-b-0 text-sm text-nature-strong opacity-70"
    >
      <i class="pi pi-arrow-down-right text-xs w-4 text-center" />
      <span class="w-24 shrink-0 text-xs">{{ $t('itinerary.agenda.continues') }}</span>
      <span class="italic">{{ cont.title }}</span>
    </div>

    <AgendaBookingSection
      v-if="lodgingRows.length"
      tone="lodging"
      icon="mdi mdi-bed"
      :title="$t('itinerary.agenda.lodging')"
      :tripId="0"
      :rows="lodgingRows"
      position="bottom"
      readonly
    />

    <p
      v-if="
        !transportRows.length &&
        !otherRows.length &&
        !lodgingRows.length &&
        !items.length &&
        !continuations.length
      "
      class="px-4 py-3 text-xs text-ink-disabled"
    >
      {{ emptyLabel }}
    </p>
  </div>
</template>
